#!/usr/bin/env python3
"""Safely deploy allowlisted static site overlays over pinned SSH."""

from __future__ import annotations

import hashlib
import base64
import os
import pathlib
import posixpath
import re
import sys
import time
import zipfile

ARCHIVE = pathlib.Path("/tmp/blog-unique-covers-jdm-update.zip")
ARCHIVE_PARTS = pathlib.Path("deploy")
KNOWN_HOSTS = pathlib.Path("deploy/jdm_known_hosts_web13")
HOST = "web13.jdm.pl"
PORT = 2233
USERNAME = "vvictgzv"
RUN_ID = os.environ.get("GITHUB_RUN_ID", str(int(time.time())))


def read_manifest(zf: zipfile.ZipFile) -> dict[str, str]:
    manifest: dict[str, str] = {}
    raw = zf.read("SHA256SUMS.txt").decode("utf-8")
    for line in raw.splitlines():
        digest, name = line.split(None, 1)
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("Invalid SHA-256 manifest")
        name = name.strip()
        manifest[name] = digest
    return manifest


def is_allowed(name: str) -> bool:
    if name in {"robots.txt", "sitemap.xml"}:
        return True
    if name == "index.html":
        return True
    if name == "assets/sales-template.html":
        return True
    if name == "test/index.html":
        return False
    if name.startswith("assets/blog/"):
        return bool(re.fullmatch(r"assets/blog/[a-z0-9-]+\.svg", name))
    if name == "blog/index.html":
        return True
    if re.fullmatch(r"blog/[a-z0-9-]+/index\.html", name):
        return True
    return bool(re.fullmatch(r"[a-z0-9][a-z0-9-]*/index\.html", name))


def prepare_files(zf: zipfile.ZipFile) -> list[tuple[str, bytes]]:
    manifest = read_manifest(zf)
    prepared: list[tuple[str, bytes]] = []
    seen_covers: set[str] = set()
    for info in zf.infolist():
        if info.is_dir() or info.filename in {"WAZNE.txt", "SHA256SUMS.txt", "test/index.html"}:
            continue
        name = info.filename
        path = pathlib.PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or not is_allowed(name):
            raise ValueError(f"Unexpected archive path: {name}")
        data = zf.read(info)
        expected = manifest.get(name)
        if not expected or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f"Checksum mismatch: {name}")
        if name.startswith("assets/blog/"):
            if data[:100].find(b"<svg") < 0:
                raise ValueError(f"Invalid SVG cover: {name}")
            seen_covers.add(hashlib.sha256(data).hexdigest())
        prepared.append((name, data))
    names = [name for name, _ in prepared]
    if seen_covers:
        if len(seen_covers) != 44:
            raise ValueError(f"Expected 44 distinct covers, found {len(seen_covers)}")
    else:
        page_names = {name for name in names if name == "index.html" or name.endswith("/index.html")}
        extras = set(names) - page_names - {"assets/sales-template.html"}
        protected = {name for name in page_names if name.startswith("wersja-pierwotna/") or name == "test/index.html" or name == "na-sprzedaz/index.html"}
        single_template = names == ["assets/sales-template.html"]
        if not single_template and (not page_names or extras or protected):
            raise ValueError("A coverless package may update only allowlisted site pages and the catalog template")
    if not prepared:
        raise ValueError("The overlay is empty")
    return prepared


def sftp_mkdirs(sftp: paramiko.SFTPClient, path: str) -> None:
    current = "/" if path.startswith("/") else ""
    for part in path.strip("/").split("/"):
        if not part:
            continue
        current = posixpath.join(current, part)
        try:
            sftp.stat(current)
        except OSError:
            sftp.mkdir(current)


def exists(sftp: paramiko.SFTPClient, path: str) -> bool:
    try:
        sftp.stat(path)
        return True
    except OSError:
        return False


def main() -> int:
    if not os.environ.get("JDM_PASSWORD"):
        raise RuntimeError("JDM_PASSWORD is not configured")
    import paramiko

    parts = sorted(ARCHIVE_PARTS.glob("blog-archive.part-*"))
    if not parts:
        raise RuntimeError("Blog archive segments are missing")
    encoded = b"".join(part.read_bytes() for part in parts)
    ARCHIVE.write_bytes(base64.b64decode(encoded, validate=True))

    with zipfile.ZipFile(ARCHIVE) as zf:
        files = prepare_files(zf)

    client = paramiko.SSHClient()
    client.load_host_keys(str(KNOWN_HOSTS))
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect(
        hostname=HOST,
        port=PORT,
        username=USERNAME,
        password=os.environ["JDM_PASSWORD"],
        look_for_keys=False,
        allow_agent=False,
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
    )
    sftp = client.open_sftp()
    stage = backup = ""
    moved_old: list[tuple[str, str]] = []
    installed: list[str] = []
    try:
        home = sftp.normalize(".").rstrip("/")
        public_root = posixpath.join(home, "public_html")
        private_root = posixpath.join(home, "private")
        if not exists(sftp, public_root) or not exists(sftp, private_root):
            raise RuntimeError("Expected public/private hosting directories were not found")
        token = re.sub(r"[^A-Za-z0-9_-]", "_", RUN_ID)
        stage = posixpath.join(private_root, f"blog-stage-{token}")
        backup = posixpath.join(private_root, f"blog-backup-{token}")
        sftp_mkdirs(sftp, stage)
        sftp_mkdirs(sftp, backup)

        for name, data in files:
            staged = posixpath.join(stage, name)
            sftp_mkdirs(sftp, posixpath.dirname(staged))
            with sftp.file(staged, "wb") as remote:
                remote.write(data)

        # Back up only the exact files that will be replaced, then install them.
        for name, _ in files:
            destination = posixpath.join(public_root, name)
            sftp_mkdirs(sftp, posixpath.dirname(destination))
            if exists(sftp, destination):
                saved = posixpath.join(backup, name)
                sftp_mkdirs(sftp, posixpath.dirname(saved))
                sftp.rename(destination, saved)
                moved_old.append((saved, destination))
        for name, _ in files:
            staged = posixpath.join(stage, name)
            destination = posixpath.join(public_root, name)
            sftp.rename(staged, destination)
            installed.append(destination)
    except Exception:
        for destination in reversed(installed):
            try:
                sftp.remove(destination)
            except OSError:
                pass
        for saved, destination in reversed(moved_old):
            try:
                sftp_mkdirs(sftp, posixpath.dirname(destination))
                sftp.rename(saved, destination)
            except OSError:
                pass
        raise
    finally:
        sftp.close()
        client.close()

    print(f"Installed {len(files)} blog files; previous versions backed up in the private hosting directory.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Blog overlay deployment failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1)
