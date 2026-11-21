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
            ("<style id=\"loan-rate-tiles-style\">\n.loan-rate-tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(8px,2vw,16px);max-width:380px;margin:28px 0 20px}\n.loan-rate-tiles .rate-note{display:flex;flex-direction:column;justify-content:flex-start;gap:7px;min-width:0;width:100%;margin:0;padding:10px 6px 15px;text-align:center;background:linear-gradient(112deg,#dfd0b8 0%,#f8f2e7 38%,#e0cba9 65%,#f4ecdf 100%);background-size:230% 100%;background-position:45% 50%}\n.loan-rate-tiles .rate-note>span{display:inline-flex;align-items:baseline;gap:.12em;letter-spacing:normal;color:#866d48;font-size:clamp(48px,6.1vw,76px);white-space:nowrap}\n.loan-rate-tiles .rate-note>span small{font-size:.46em}\n.loan-rate-tiles .rate-note>div{font-size:clamp(15px,1.3vw,17px);line-height:1.2;font-weight:400;color:#746653;white-space:nowrap}\n@media(prefers-reduced-motion:no-preference){.loan-rate-tiles .rate-note{animation:loan-rate-sheen 12s ease-in-out infinite alternate}}\n@keyframes loan-rate-sheen{from{background-position:12% 50%}to{background-position:88% 50%}}\n.page-home-calculator .calculator .amount-field{align-items:center;margin-top:8px;border:1px solid #b5a48a;border-radius:4px;background:#fff;padding:0 12px 0 0}\n.page-home-calculator .calculator .amount-field:focus-within{border-color:#866d48;box-shadow:0 0 0 2px #866d4833}\n.page-home-calculator .calculator .amount-field input{padding:10px 12px;min-height:56px;font-size:36px;border-radius:4px;outline:none}\n.page-home-calculator .calculator .amount-field input::placeholder{font:500 17px/1.2 SezamSans,Arial,sans-serif;letter-spacing:normal;color:#686054}\n.loan-rate-tiles .rate-caption{margin:0;color:#746653;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}\n.page-home-calculator .calculator .amount-presets button{min-height:36px;font-size:clamp(10px,1vw,13px);padding:7px 1px}\n.page-home-calculator .calculator .segmented{background:#f2e7d6;gap:3px}\n.page-home-calculator .calculator .segmented button{min-height:40px;padding:8px clamp(12px,2.1vw,26px);font-size:14px;color:#604c30}\n.page-home-calculator .calculator .segmented button.selected{background:#d9bd8f;color:#3e2d17;font-weight:700}\n</style>", "<style id=\"loan-rate-tiles-style\">\n.loan-rate-tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(8px,2vw,16px);max-width:380px;margin:28px 0 20px}\n.loan-rate-tiles .rate-note{display:grid;grid-template-rows:auto 1fr auto;justify-items:center;gap:3px;min-width:0;width:100%;margin:0;padding:13px 10px 0;text-align:center;border:1px solid #bc9a65;border-top:3px solid #a87b3d;box-shadow:inset 0 1px 0 #fff8,0 6px 16px #6747191a;background:linear-gradient(112deg,#ddc39b 0%,#fff7e8 34%,#e0c599 68%,#f3e5cc 100%);background-size:230% 100%;background-position:45% 50%}\n.loan-rate-tiles .rate-note>span{display:inline-flex;align-items:baseline;gap:.12em;letter-spacing:normal;align-self:start;position:relative;top:-3px;color:#76572f;font-size:clamp(48px,6.1vw,76px);white-space:nowrap}\n.loan-rate-tiles .rate-note>span small{font-size:.46em}\n.loan-rate-tiles .rate-note>div{justify-self:stretch;margin:3px -10px 0;padding:8px 4px 9px;border-top:1px solid #a87b3d55;background:#a87b3d20;font-size:clamp(15px,1.3vw,17px);line-height:1.2;font-weight:500;color:#694d2b;white-space:nowrap}\n@media(prefers-reduced-motion:no-preference){.loan-rate-tiles .rate-note{animation:loan-rate-sheen 12s ease-in-out infinite alternate}}\n@keyframes loan-rate-sheen{from{background-position:12% 50%}to{background-position:88% 50%}}\n.page-home-calculator .calculator .amount-field{align-items:center;margin-top:8px;border:1px solid #b5a48a;border-radius:4px;background:#fff;padding:0 12px 0 0}\n.page-home-calculator .calculator .amount-field:focus-within{border-color:#866d48;box-shadow:0 0 0 2px #866d4833}\n.page-home-calculator .calculator .amount-field input{padding:10px 12px;min-height:56px;font-size:36px;border-radius:4px;outline:none}\n.page-home-calculator .calculator .amount-field input::placeholder{font:500 17px/1.2 SezamSans,Arial,sans-serif;letter-spacing:normal;color:#686054}\n.loan-rate-tiles .rate-caption{margin:0;color:#746653;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}\n.page-home-calculator .calculator .amount-presets button{min-height:36px;font-size:clamp(10px,1vw,13px);padding:7px 1px}\n.page-home-calculator .calculator .segmented{background:#f2e7d6;gap:3px}\n.page-home-calculator .calculator .segmented button{min-height:40px;padding:8px clamp(12px,2.1vw,26px);font-size:14px;color:#604c30}\n.page-home-calculator .calculator .segmented button.selected{background:#d9bd8f;color:#3e2d17;font-weight:700}\n.page-home-calculator .calculator .amount-presets{grid-template-columns:repeat(6,minmax(0,1fr));margin-bottom:10px}\n.page-home-calculator .calculator .amount-presets button{white-space:nowrap}\n.page-home-calculator .calculator .amount-negotiation{margin:0 0 20px;color:#65563f;font-size:13px;line-height:1.5}\n.page-home-calculator .calculator .amount-negotiation a{color:#75552b;text-decoration:underline;text-underline-offset:2px;font-weight:700}\n</style>"),
            ("<div class=\"amount-presets\" aria-label=\"Gotowe kwoty\"><button type=\"button\" data-amount=\"100\" aria-pressed=\"false\">100</button><button type=\"button\" data-amount=\"200\" aria-pressed=\"false\">200</button><button type=\"button\" data-amount=\"500\" aria-pressed=\"false\">500</button><button type=\"button\" data-amount=\"1000\" aria-pressed=\"false\">1 000</button><button type=\"button\" data-amount=\"1500\" aria-pressed=\"false\">1 500</button><button type=\"button\" data-amount=\"2000\" aria-pressed=\"false\">2 000</button><button type=\"button\" data-amount=\"3000\" aria-pressed=\"false\">3 000</button><button type=\"button\" data-amount=\"5000\" aria-pressed=\"false\">5 000</button><button type=\"button\" data-amount=\"7000\" aria-pressed=\"false\">7 000</button><button type=\"button\" data-amount=\"10000\" aria-pressed=\"false\">10 000</button></div>", "<div class=\"amount-presets\" aria-label=\"Gotowe kwoty\"><button type=\"button\" data-amount=\"100\" aria-pressed=\"false\">100</button><button type=\"button\" data-amount=\"200\" aria-pressed=\"false\">200</button><button type=\"button\" data-amount=\"500\" aria-pressed=\"false\">500</button><button type=\"button\" data-amount=\"1000\" aria-pressed=\"false\">1 000</button><button type=\"button\" data-amount=\"1500\" aria-pressed=\"false\">1 500</button><button type=\"button\" data-amount=\"2000\" aria-pressed=\"false\">2 000</button><button type=\"button\" data-amount=\"3000\" aria-pressed=\"false\">3 000</button><button type=\"button\" data-amount=\"5000\" aria-pressed=\"false\">5 000</button><button type=\"button\" data-amount=\"7000\" aria-pressed=\"false\">7 000</button><button type=\"button\" data-amount=\"10000\" aria-pressed=\"false\">10 000</button><button type=\"button\" data-amount=\"20000\" aria-pressed=\"false\">20 000</button><button type=\"button\" data-amount=\"50000\" aria-pressed=\"false\">50 000</button></div><p class=\"amount-negotiation\"><strong>Potrzebujesz większej kwoty?</strong> Opłata do negocjacji. <a href=\"tel:+48601775146\">Zadzwoń</a></p>"),
        ]
        if all(current.count(new) == 1 for _, new in changes):
            print("Homepage already has the updated rates and presets.")
            return 0
        updated = current
        for old, new in changes:
            if updated.count(old) != 1:
                raise RuntimeError("The live homepage did not match the expected calculator markup.")
            updated = updated.replace(old, new, 1)
        files = [("index.html", updated.encode("utf-8"))]
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
