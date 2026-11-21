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
.gold-pricing{padding-top:12px}
.gold-pricing .price-heading h1{margin-top:0}
.page-kontakt footer .footer-navigation{margin-block:0;padding-block:20px}
</style>"""

def polish_page(page, name):
    if 'id="i-whatsapp"' not in page or '</head>' not in page:
        return page
    if name in ('na-sprzedaz/index.html', 'assets/sales-template.html'):
        if 'id="sezam-sales-whatsapp"' not in page:
            page = page.replace('</head>', "<script id=\"sezam-sales-whatsapp\">document.addEventListener(\"DOMContentLoaded\",()=>{document.querySelectorAll('.sales-actions a[href^=\"https://wa.me/\"]:not(.wa-action)').forEach(link=>{const icon=document.querySelector(\".header-whatsapp .wa-icon\");if(!icon)return;const label=document.createElement(\"span\");label.textContent=\"Napisz na WhatsApp\";link.classList.add(\"wa-action\");link.replaceChildren(icon.cloneNode(true),label)})})</script>" + '\n</head>', 1)
    if name == 'co-przyjmujemy/index.html':
        pin = ".accepted-question a.wa-action.accepted-whatsapp{background:#00854a;color:#fff;border-color:#00854a}\n.accepted-question a.wa-action.accepted-whatsapp:hover{background:#006d3d;color:#fff;border-color:#006d3d}"
        marker = '<style id="sezam-whatsapp-and-page-polish">'
        if marker in page and pin not in page:
            page = page.replace(marker, marker + '\n' + pin, 1)
    if 'id="sezam-whatsapp-and-page-polish"' in page:
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
    if name == 'co-przyjmujemy/index.html':
        style = WA_STYLE.replace('</style>', ".accepted-question a.wa-action.accepted-whatsapp{background:#00854a;color:#fff;border-color:#00854a}\n.accepted-question a.wa-action.accepted-whatsapp:hover{background:#006d3d;color:#fff;border-color:#006d3d}" + '\n</style>', 1)
    else:
        style = WA_STYLE
    return page.replace('</head>', style + '\n</head>', 1)


STYLE = """<style id="sezam-site-buttons-v2">
body a.wa-action,body button.wa-action,body .contact-grid a.wa-action.contact-whatsapp,body .accepted-question a.wa-action.accepted-whatsapp,body .mobile-bar button.wa-action,body .whatsapp-float .whatsapp-bubble,body .whatsapp-float .whatsapp-circle{background:#25d366;color:#fff;border-color:#25d366;text-shadow:0 1px 2px #075831,0 0 2px #075831}
body a.wa-action,body button.wa-action,body .contact-grid a.wa-action.contact-whatsapp,body .accepted-question a.wa-action.accepted-whatsapp,body .mobile-bar button.wa-action{border-radius:9px}
body a.wa-action:hover,body button.wa-action:hover,body .contact-grid a.wa-action.contact-whatsapp:hover,body .accepted-question a.wa-action.accepted-whatsapp:hover,body .mobile-bar button.wa-action:hover{background:#2be171;color:#fff;border-color:#2be171}
body .wa-action .wa-icon,body .whatsapp-float .wa-icon{color:#fff;filter:drop-shadow(0 1px 1px #087641)}
body .mobile-bar a,body .mobile-bar a:nth-child(2){border-radius:9px}
body.page-home-calculator a.wa-action,body.page-home-calculator button.wa-action,body.page-home-calculator .contact-grid a.wa-action.contact-whatsapp,body.page-home-calculator .mobile-bar button.wa-action,body.page-home-calculator .whatsapp-float .whatsapp-bubble,body.page-home-calculator .whatsapp-float .whatsapp-circle{color:#fff}
body.page-home-calculator a.wa-action:hover,body.page-home-calculator button.wa-action:hover,body.page-home-calculator .contact-grid a.wa-action.contact-whatsapp:hover,body.page-home-calculator .mobile-bar button.wa-action:hover{color:#fff}
.gold-pricing .price-actions{display:grid;grid-template-columns:1fr;gap:8px}
.gold-pricing .price-actions>a{width:100%;margin:0;justify-content:center;border-radius:9px}
.gold-pricing .price-actions .price-call{background:linear-gradient(112deg,#ad9167 0%,#e9dbc2 30%,#c3aa83 57%,#e0ceb0 78%,#b69b73 100%);color:#403321;border:1px solid #9b835f}
.page-kalkulator .amount-presets{grid-template-columns:repeat(6,minmax(0,1fr))}
.page-kalkulator .amount-presets button{min-height:36px;font-size:clamp(10px,1vw,13px);padding:7px 1px;white-space:nowrap}
</style>"""

def refine(page, name, rates_css):
    if 'id="i-whatsapp"' not in page or 'id="sezam-site-buttons-v2"' in page:
        return page
    page = re.sub(r'/assets/sezam-logo-square\.webp(?:\?v=[a-f0-9]+)?', '/assets/sezam-logo-hd.webp', page)
    if name == 'kontakt/index.html':
        page = page.replace('<span class="eyebrow">WPADNIJ PO SĄSIEDZKU</span>', '', 1)
    if name == 'cennik-zlota/index.html':
        page = re.sub(r'(<div class="price-actions">)(<a\b[^>]*\bid="price-whatsapp"[^>]*>.*?</a>)(<a\b[^>]*\bhref="tel:[^"]*"[^>]*>.*?</a>)', lambda m: m[1]+m[3].replace('btn-dark','price-call',1)+m[2], page, count=1, flags=re.S)
    extra = STYLE
    if name == 'kalkulator/index.html':
        extra += '<style id="sezam-standalone-rates">'+rates_css+'</style>'
    return page.replace('</head>', extra+'\n</head>', 1)


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
        style = "<style id=\"sezam-mobile-menu-icons\">\n@media(max-width:760px){\n#main-nav>a{display:flex;align-items:center;gap:12px}\n#main-nav>a::before{content:\"\";width:20px;height:20px;flex:0 0 20px;background:#806849;mask:var(--nav-icon) center/contain no-repeat}\n#main-nav>a:not([href])::before{content:none}\n#main-nav>a[href=\"/co-przyjmujemy/\"]{--nav-icon:url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.45%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M4%2013h4l3%202h3a2%202%200%200%200%200-4h-3l-2-2H4m0%204v5h5l4%202%206-4a2%202%200%200%200-2-3l-2%201%22%2F%3E%3C%2Fsvg%3E\")}\n#main-nav>a[href=\"/cennik-zlota/\"]{--nav-icon:url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.45%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M6%209h12l3%208H3l3-8Zm3%204h6%22%2F%3E%3C%2Fsvg%3E\")}\n#main-nav>a[href=\"/obraczki/\"]{--nav-icon:url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.45%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Ccircle%20cx%3D%229%22%20cy%3D%2212%22%20r%3D%225%22%2F%3E%3Cpath%20d%3D%22M12%208.2a5%205%200%201%201%200%207.6%22%2F%3E%3C%2Fsvg%3E\")}\n#main-nav>a[href=\"/na-sprzedaz/\"]{--nav-icon:url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.45%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M5%208h14l1%2012H4L5%208Zm4%201V6a3%203%200%200%201%206%200v3%22%2F%3E%3C%2Fsvg%3E\")}\n#main-nav>a[href=\"/kalkulator/\"]{--nav-icon:url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.45%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Crect%20x%3D%225%22%20y%3D%223%22%20width%3D%2214%22%20height%3D%2218%22%20rx%3D%222%22%2F%3E%3Cpath%20d%3D%22M8%207h8m-7%205h.01m3%200h.01m3%200h.01m-6%204h.01m3%200h.01m3%200h.01%22%2F%3E%3C%2Fsvg%3E\")}\n#main-nav>a[href=\"/blog/\"]{--nav-icon:url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.45%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M6%203h8l4%204v14H6V3Zm8%200v5h4M9%2012h6m-6%204h6%22%2F%3E%3C%2Fsvg%3E\")}\n#main-nav>a[href=\"/kontakt/\"]{--nav-icon:url(\"data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20viewBox%3D%220%200%2024%2024%22%20fill%3D%22none%22%20stroke%3D%22black%22%20stroke-width%3D%221.45%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%3E%3Cpath%20d%3D%22M19%2011c0%204-7%209-7%209s-7-5-7-9a7%207%200%200%201%2014%200Z%22%2F%3E%3Ccircle%20cx%3D%2212%22%20cy%3D%2211%22%20r%3D%222%22%2F%3E%3C%2Fsvg%3E\")}\n}\n</style>"
        files = []
        for name in ["index.html","assets/sales-template.html","13789-2/index.html","blog/index.html","cennik-zlota/index.html","co-mozna-zastawic-w-lombardzie-w-gorzowie/index.html","co-przyjmujemy/index.html","czesci-do-telefonow/index.html","czym-polega-dzialalnosc-lombardu/index.html","dlaczego-lombard-w-gorzowie-sa-chetnie-odwiedzane/index.html","galeria/index.html","gdzie-mozna-zdobyc-szybko-pieniadze/index.html","jak-oszacowac-wartosc-bizuterii-zlotej-monet-sztabek/index.html","jak-powstalo-zloto/index.html","kalkulator/index.html","kontakt/index.html","kto-przoduje-w-wydobywaniu-zlota/index.html","lombard-gorzow/index.html","lombard-gorzow-jak-szybko-uzyskac-gotowke-pod-zastaw/index.html","lombard-gorzow-lombardy-polsce-swiecie/index.html","lombard-w-gorzowie-telefony-i-laptopy-pod-zastaw/index.html","lombardy-zloto-wyglada/index.html","mowa-ojczysta-zlotem-okraszona-skup-zlota-gorzow/index.html","na-sprzedaz/index.html","nowosc-monety/index.html","o-nas/index.html","obraczki/index.html","oferta/index.html","pierscionki-zareczynowe/index.html","pochodzenie-zlota/index.html","podrabiane-sztabki-jeszcze/index.html","poszukiwanie-dobrego-lombardu/index.html","pozyczka-od-reki/index.html","pozyczki-zastaw-lombardzie-lombard-gorzow/index.html","produkcja-wyrobow-ze-zlota/index.html","pytania/index.html","rozwoj-lombardow/index.html","serwis-telefonow-gorzow/index.html","skup-laptopow-gorzow/index.html","skup-telefonow-gorzow/index.html","skup-zlota-dziala/index.html","skup-zlota-gorzow/index.html","skup-zlota-gorzow-aktualne-ceny/index.html","skup-zlota-gorzow-wlkp/index.html","skup-zlota-gorzow-wydobycie-zlota-az-po-jego-skup/index.html","skup-zlota-gorzow-zlote-skoki-czyli-najwieksze-rabunki/index.html","skup-zlota-w-gorzowie-na-co-zwrocic-uwage-przy-wycenie/index.html","skup-zlota-w-punkcie-skupu-czy-warto/index.html","test/index.html","wydobycie-i-znaczenie-zlota-na-swiecie/index.html","wykorzystanie-zlota-medycynie-skup-zlota-gorzow/index.html","zastosowanie-zlota-przemysle-elektronicznym/index.html","zlote-dodatki-modzie/index.html","zloto-elektronice-skup-zlota-gorzow/index.html","zloto-inwestycyjne-uzytkowe-w-lombard-gorzow/index.html","zloto-jubilerstwie-skup-zlota-gorzow/index.html","zloto-medycynie-skup-zlota-gorzow/index.html","zloto-moda-skup-zlota-gorzow/index.html","zloto-popularnosc-na-swiecie/index.html","zloto-w-gastronomii/index.html","blog/od-czego-zalezy-wycena-zlota/index.html","blog/pierwsza-wizyta-w-lombardzie/index.html","blog/telefon-laptop-przygotowanie-do-wyceny/index.html","blog/zastaw-czy-sprzedaz-przedmiotu/index.html"]:
            target = posixpath.join(public_root, name)
            if not exists(sftp, target):
                if name == "index.html":
                    raise RuntimeError("The homepage was not found.")
                continue
            with sftp.file(target, "rb") as remote:
                current = remote.read().decode("utf-8")
            if 'id="main-nav"' not in current or style in current:
                continue
            if current.count("</head>") != 1:
                raise RuntimeError(f"Unexpected markup in {name}")
            updated = current.replace("</head>", style + "\n</head>", 1)
            files.append((name, updated.encode("utf-8")))
        if not files:
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
