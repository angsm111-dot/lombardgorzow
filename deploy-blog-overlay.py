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


WA_ICON = '<svg class="wa-icon" aria-hidden="true"><use href="#i-whatsapp"/></svg>'
WA_LABEL = 'Napisz na WhatsApp'
WA_STYLE = """<style id="sezam-whatsapp-and-page-polish">
a.wa-action,button.wa-action,.mobile-bar button.wa-action{display:inline-flex;align-items:center;justify-content:center;gap:7px;background:#00854a;color:#fff;border:1px solid #00854a;text-decoration:none}
a.wa-action:hover,button.wa-action:hover,.mobile-bar button.wa-action:hover{background:#006d3d;color:#fff;border-color:#006d3d}
.wa-action .wa-icon{width:20px;height:20px;flex:none;color:inherit}
a.wa-action.text-link,a.wa-action.accepted-inquiry{padding:9px 13px;width:fit-content}
.mobile-bar button.wa-action{flex-direction:column;gap:3px}
.whatsapp-float .whatsapp-bubble,.whatsapp-float .whatsapp-circle{background:#00854a;color:#fff;border-color:#00854a}
.contact-grid a.wa-action.contact-whatsapp{background:#00854a;color:#fff;border-color:#00854a}
.contact-grid a.wa-action.contact-whatsapp:hover{background:#006d3d;color:#fff;border-color:#006d3d}
.gold-pricing{padding-top:12px}
.gold-pricing .price-heading h1{margin-top:0}
.page-kontakt footer .footer-navigation{margin-block:0;padding-block:20px}
</style>"""

def polish_page(page, name):
    if 'id="i-whatsapp"' not in page or '</head>' not in page:
        return page
    if 'id="sezam-whatsapp-and-page-polish"' in page:
        old_rule = ".whatsapp-float .whatsapp-bubble,.whatsapp-float .whatsapp-circle{background:#00854a;color:#fff;border-color:#00854a}"
        extra_rules = ".contact-grid a.wa-action.contact-whatsapp{background:#00854a;color:#fff;border-color:#00854a}\n.contact-grid a.wa-action.contact-whatsapp:hover{background:#006d3d;color:#fff;border-color:#006d3d}"
        if "wa-action btn contact-whatsapp" in page and extra_rules not in page:
            return page.replace(old_rule, old_rule + "\n" + extra_rules, 1)
        return page

    def whatsapp_link(match):
        start, content = match.groups()
        if 'whatsapp-float' in start:
            return start + content.replace('>Napisz wiadomość<', '>WhatsApp<', 1) + '</a>'
        label = 'WhatsApp' if 'header-whatsapp' in start else WA_LABEL
        if ' data-' in start and 'header-whatsapp' not in start:
            return match.group(0)
        if ' class="' in start:
            start = start.replace(' class="', ' class="wa-action ', 1)
        else:
            start = start.replace('<a ', '<a class="wa-action" ', 1)
        return start + WA_ICON + '<span>' + label + '</span></a>'

    page = re.sub(r'(<a\b[^>]*\bhref="https://(?:wa\.me|api\.whatsapp\.com)/[^"]*"[^>]*>)(.*?)</a>', whatsapp_link, page, flags=re.S)
    page = re.sub(
        r'<button class="btn btn-blue" type="submit">Przejdź do WhatsApp .*?</button>',
        '<button class="btn wa-action" type="submit">' + WA_ICON + '<span>' + WA_LABEL + '</span></button>',
        page, flags=re.S,
    )
    page = page.replace(
        '<button data-inquiry="Wycena przedmiotu"><svg><use href="#i-chat"/></svg>Napisz</button>',
        '<button class="wa-action" data-inquiry="Wycena przedmiotu">' + WA_ICON + '<span>WhatsApp</span></button>',
    )
    if name == 'kontakt/index.html':
        page = re.sub(r'<footer>.*?(<nav class="wrap footer-navigation".*?</nav>).*?</footer>', r'<footer>\1</footer>', page, count=1, flags=re.S)
    if name == 'cennik-zlota/index.html':
        page = re.sub(r'<span class="eyebrow muted">ZŁOTO · SREBRO · MONETY · SZTABKI</span>\s*', '', page, count=1)
        page = re.sub(r'(<div class="section-heading price-heading"[^>]*>\s*<div>)<h1>.*?</h1>', r'\1<h1>Sprawdź, ile warte jest<br><span class="soft">Twoje złoto.</span></h1>', page, count=1, flags=re.S)
    return page.replace('</head>', WA_STYLE + '\n</head>', 1)


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
        routes = ["index.html", "kontakt/index.html"]
        files = []
        for name in routes:
            page_path = posixpath.join(public_root, name)
            if not exists(sftp, page_path):
                continue
            with sftp.file(page_path, "rb") as remote:
                current = remote.read().decode("utf-8")
            updated = polish_page(current, name)
            if updated != current:
                files.append((name, updated.encode("utf-8")))
        if not files:
            print("No pages needed changes.")
            return 0
        token = re.sub(r"[^A-Za-z0-9_-]", "_", RUN_ID)
        stage = posixpath.join(private_root, f"contact-ui-stage-{token}")
        backup = posixpath.join(private_root, f"contact-ui-backup-{token}")
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
