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
        homepage = posixpath.join(public_root, "index.html")
        with sftp.file(homepage, "rb") as remote:
            current = remote.read().decode("utf-8")
        changes = [
            ("<div class=\"loan-rate-tiles\">\n  <div class=\"rate-note\"><span>2,5<small>%</small></span><div><svg class=\"rate-calendar\" viewBox=\"0 0 24 24\" aria-hidden=\"true\" focusable=\"false\"><rect x=\"4\" y=\"6\" width=\"16\" height=\"14\" rx=\"1\"/><path d=\"M8 4v4m8-4v4M4 10h16m-11 5h.01m3 0h.01m3 0h.01\"/></svg><span>za 15 dni</span></div></div>\n  <div class=\"rate-note\"><span>5<small>%</small></span><div><svg class=\"rate-calendar\" viewBox=\"0 0 24 24\" aria-hidden=\"true\" focusable=\"false\"><rect x=\"4\" y=\"6\" width=\"16\" height=\"14\" rx=\"1\"/><path d=\"M8 4v4m8-4v4M4 10h16m-11 5h.01m3 0h.01m3 0h.01\"/></svg><span>za 30 dni</span></div></div>\n</div>", "<div class=\"loan-rate-tiles\">\n  <div class=\"rate-note\"><span>2,5<small>%</small></span><div><span>za 15 dni</span></div></div>\n  <div class=\"rate-note\"><span>5<small>%</small></span><div><span>za 30 dni</span></div></div>\n</div>"),
            ("<style id=\"loan-rate-tiles-style\">\n.loan-rate-tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(8px,2vw,16px);max-width:380px;margin:28px 0 20px}\n.loan-rate-tiles .rate-note{display:flex;flex-direction:column;justify-content:center;gap:6px;min-width:0;width:100%;margin:0;padding:14px 6px;text-align:center}\n.loan-rate-tiles .rate-note>span{display:inline-flex;align-items:baseline;gap:.12em;letter-spacing:normal;font-size:clamp(43px,5.5vw,69px);white-space:nowrap}\n.loan-rate-tiles .rate-note>span small{font-size:.46em}\n.loan-rate-tiles .rate-note>div{display:flex;align-items:center;justify-content:center;gap:6px;font-size:14px;line-height:1.35;white-space:nowrap}\n.loan-rate-tiles .rate-calendar{width:17px;height:17px;flex:none;color:#866d48;stroke-width:1.45}\n</style>", "<style id=\"loan-rate-tiles-style\">\n.loan-rate-tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(8px,2vw,16px);max-width:380px;margin:28px 0 20px}\n.loan-rate-tiles .rate-note{display:flex;flex-direction:column;justify-content:flex-start;gap:7px;min-width:0;width:100%;margin:0;padding:10px 6px 15px;text-align:center;background:linear-gradient(112deg,#dfd0b8 0%,#f8f2e7 38%,#e0cba9 65%,#f4ecdf 100%);background-size:230% 100%;background-position:45% 50%}\n.loan-rate-tiles .rate-note>span{display:inline-flex;align-items:baseline;gap:.12em;letter-spacing:normal;font-size:clamp(48px,6.1vw,76px);white-space:nowrap}\n.loan-rate-tiles .rate-note>span small{font-size:.46em}\n.loan-rate-tiles .rate-note>div{font-size:clamp(15px,1.3vw,17px);line-height:1.2;font-weight:600;white-space:nowrap}\n@media(prefers-reduced-motion:no-preference){.loan-rate-tiles .rate-note{animation:loan-rate-sheen 12s ease-in-out infinite alternate}.loan-rate-tiles .rate-note:nth-child(2){animation-delay:-4s}}\n@keyframes loan-rate-sheen{from{background-position:12% 50%}to{background-position:88% 50%}}\n.page-home-calculator .calculator .amount-field{align-items:center;margin-top:8px;border:1px solid #b5a48a;border-radius:4px;background:#fff;padding:0 12px 0 0}\n.page-home-calculator .calculator .amount-field:focus-within{border-color:#866d48;box-shadow:0 0 0 2px #866d4833}\n.page-home-calculator .calculator .amount-field input{padding:10px 12px;min-height:56px;font-size:36px;border-radius:4px;outline:none}\n.page-home-calculator .calculator .amount-field input::placeholder{font:500 17px/1.2 SezamSans,Arial,sans-serif;letter-spacing:normal;color:#686054}\n</style>"),
            ("value=\"2000\" inputmode=\"decimal\" aria-describedby=\"amount-error\"", "placeholder=\"Wpisz kwotę\" inputmode=\"decimal\" aria-describedby=\"amount-error\""),
            ("id=\"amount-range\" min=\"50\" max=\"20000\" step=\"50\" value=\"2000\"", "id=\"amount-range\" min=\"50\" max=\"20000\" step=\"50\" value=\"50\""),
            ("data-amount=\"2000\" class=\"selected\" aria-pressed=\"true\"", "data-amount=\"2000\" aria-pressed=\"false\""),
            ("id=\"fee\">50,00 zł", "id=\"fee\">—"),
            ("id=\"total\">2 050,00 zł", "id=\"total\">—"),
        ]
        app_path = posixpath.join(public_root, "app.js")
        with sftp.file(app_path, "rb") as remote:
            app = remote.read().decode("utf-8")
        old_calc = "  const amount=Number($('#amount').value),valid=Number.isFinite(amount)&&amount>=50&&amount<=100000;\n  $('#amount-error').hidden=valid;$('#amount').setAttribute('aria-invalid',String(!valid));"
        new_calc = "  const field=$('#amount'),amount=field.valueAsNumber,valid=Number.isFinite(amount)&&amount>=50&&amount<=100000;\n  const invalid=!valid&&(field.value!==''||field.validity.badInput);\n  $('#amount-error').hidden=!invalid;field.setAttribute('aria-invalid',String(invalid));"
        if app.count(old_calc) == 1:
            app = app.replace(old_calc, new_calc, 1)
        elif app.count(new_calc) != 1:
            raise RuntimeError("The live calculator script did not match the expected source.")
        app_version = hashlib.sha256(app.encode("utf-8")).hexdigest()[:12]
        if all(current.count(new) == 1 for _, new in changes):
            print("Homepage already has the updated rate cards and calculator.")
            return 0
        updated = current
        for old, new in changes:
            if updated.count(old) != 1:
                raise RuntimeError("The homepage did not match the expected markup for a replacement.")
            updated = updated.replace(old, new, 1)
        updated, references = re.subn(r'/app\.js(?:\?v=[a-f0-9]+)?"', f'/app.js?v={app_version}"', updated)
        if references != 1:
            raise RuntimeError("Expected one homepage calculator script reference.")
        files = [("app.js", app.encode("utf-8")), ("index.html", updated.encode("utf-8"))]
        token = re.sub(r"[^A-Za-z0-9_-]", "_", RUN_ID)
        stage = posixpath.join(private_root, f"rate-tiles-stage-{token}")
        backup = posixpath.join(private_root, f"rate-tiles-backup-{token}")
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

    print(f"Installed {len(files)} homepage file; previous versions backed up in the private hosting directory.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Homepage rate-card deployment failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1)
