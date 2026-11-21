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
        logo_path = "assets/sezam-logo-hd.webp"
        files = [(logo_path, base64.b64decode("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", validate=True))]
        for name in ["index.html","assets/sales-template.html","13789-2/index.html","blog/index.html","cennik-zlota/index.html","co-mozna-zastawic-w-lombardzie-w-gorzowie/index.html","co-przyjmujemy/index.html","czesci-do-telefonow/index.html","czym-polega-dzialalnosc-lombardu/index.html","dlaczego-lombard-w-gorzowie-sa-chetnie-odwiedzane/index.html","galeria/index.html","gdzie-mozna-zdobyc-szybko-pieniadze/index.html","jak-oszacowac-wartosc-bizuterii-zlotej-monet-sztabek/index.html","jak-powstalo-zloto/index.html","kalkulator/index.html","kontakt/index.html","kto-przoduje-w-wydobywaniu-zlota/index.html","lombard-gorzow/index.html","lombard-gorzow-jak-szybko-uzyskac-gotowke-pod-zastaw/index.html","lombard-gorzow-lombardy-polsce-swiecie/index.html","lombard-w-gorzowie-telefony-i-laptopy-pod-zastaw/index.html","lombardy-zloto-wyglada/index.html","mowa-ojczysta-zlotem-okraszona-skup-zlota-gorzow/index.html","na-sprzedaz/index.html","nowosc-monety/index.html","o-nas/index.html","obraczki/index.html","oferta/index.html","pierscionki-zareczynowe/index.html","pochodzenie-zlota/index.html","podrabiane-sztabki-jeszcze/index.html","poszukiwanie-dobrego-lombardu/index.html","pozyczka-od-reki/index.html","pozyczki-zastaw-lombardzie-lombard-gorzow/index.html","produkcja-wyrobow-ze-zlota/index.html","pytania/index.html","rozwoj-lombardow/index.html","serwis-telefonow-gorzow/index.html","skup-laptopow-gorzow/index.html","skup-telefonow-gorzow/index.html","skup-zlota-dziala/index.html","skup-zlota-gorzow/index.html","skup-zlota-gorzow-aktualne-ceny/index.html","skup-zlota-gorzow-wlkp/index.html","skup-zlota-gorzow-wydobycie-zlota-az-po-jego-skup/index.html","skup-zlota-gorzow-zlote-skoki-czyli-najwieksze-rabunki/index.html","skup-zlota-w-gorzowie-na-co-zwrocic-uwage-przy-wycenie/index.html","skup-zlota-w-punkcie-skupu-czy-warto/index.html","test/index.html","wydobycie-i-znaczenie-zlota-na-swiecie/index.html","wykorzystanie-zlota-medycynie-skup-zlota-gorzow/index.html","zastosowanie-zlota-przemysle-elektronicznym/index.html","zlote-dodatki-modzie/index.html","zloto-elektronice-skup-zlota-gorzow/index.html","zloto-inwestycyjne-uzytkowe-w-lombard-gorzow/index.html","zloto-jubilerstwie-skup-zlota-gorzow/index.html","zloto-medycynie-skup-zlota-gorzow/index.html","zloto-moda-skup-zlota-gorzow/index.html","zloto-popularnosc-na-swiecie/index.html","zloto-w-gastronomii/index.html","blog/od-czego-zalezy-wycena-zlota/index.html","blog/pierwsza-wizyta-w-lombardzie/index.html","blog/telefon-laptop-przygotowanie-do-wyceny/index.html","blog/zastaw-czy-sprzedaz-przedmiotu/index.html"]:
            page_path = posixpath.join(public_root, name)
            if not exists(sftp, page_path):
                if name in ("index.html", "kalkulator/index.html", "kontakt/index.html", "cennik-zlota/index.html"):
                    raise RuntimeError(f"Missing production page: {name}")
                continue
            with sftp.file(page_path, "rb") as remote:
                current = remote.read().decode("utf-8")
            updated = refine(current, name, ".loan-rate-tiles{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(8px,2vw,16px);max-width:380px;margin:28px 0 20px}\n.loan-rate-tiles .rate-note{display:grid;grid-template-rows:auto 1fr auto;justify-items:center;gap:3px;min-width:0;width:100%;margin:0;padding:13px 10px 0;text-align:center;border:1px solid #bc9a65;border-top:3px solid #a87b3d;box-shadow:inset 0 1px 0 #fff8,0 6px 16px #6747191a;background:linear-gradient(112deg,#ddc39b 0%,#fff7e8 34%,#e0c599 68%,#f3e5cc 100%);background-size:230% 100%;background-position:45% 50%}\n.loan-rate-tiles .rate-note>span{display:inline-flex;align-items:baseline;gap:.12em;letter-spacing:normal;align-self:start;position:relative;top:-3px;color:#76572f;font-size:clamp(48px,6.1vw,76px);white-space:nowrap}\n.loan-rate-tiles .rate-note>span small{font-size:.46em}\n.loan-rate-tiles .rate-note>div{justify-self:stretch;margin:3px -10px 0;padding:8px 4px 9px;border-top:1px solid #a87b3d55;background:#a87b3d20;font-size:clamp(15px,1.3vw,17px);line-height:1.2;font-weight:500;color:#694d2b;white-space:nowrap}\n@media(prefers-reduced-motion:no-preference){.loan-rate-tiles .rate-note{animation:loan-rate-sheen 12s ease-in-out infinite alternate}}\n@keyframes loan-rate-sheen{from{background-position:12% 50%}to{background-position:88% 50%}}\n.loan-rate-tiles .rate-caption{margin:0;color:#746653;font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase}")
            if name == "kalkulator/index.html" and updated != current:
                updated, rate_count = re.subn(r'<div class="rate-note">.*?</div></div>', lambda _: "<div class=\"loan-rate-tiles\">\n  <div class=\"rate-note\"><p class=\"rate-caption\">Opłata</p><span>2,5<small>%</small></span><div><span>za 15 dni</span></div></div>\n  <div class=\"rate-note\"><p class=\"rate-caption\">Opłata</p><span>5<small>%</small></span><div><span>za 30 dni</span></div></div>\n</div>", updated, count=1, flags=re.S)
                updated, preset_count = re.subn(r'<div class="amount-presets"[^>]*>.*?</div>', lambda _: "<div class=\"amount-presets\" aria-label=\"Gotowe kwoty\"><button type=\"button\" data-amount=\"100\" aria-pressed=\"false\">100</button><button type=\"button\" data-amount=\"200\" aria-pressed=\"false\">200</button><button type=\"button\" data-amount=\"500\" aria-pressed=\"false\">500</button><button type=\"button\" data-amount=\"1000\" aria-pressed=\"false\">1 000</button><button type=\"button\" data-amount=\"1500\" aria-pressed=\"false\">1 500</button><button type=\"button\" data-amount=\"2000\" class=\"selected\" aria-pressed=\"true\">2 000</button><button type=\"button\" data-amount=\"3000\" aria-pressed=\"false\">3 000</button><button type=\"button\" data-amount=\"5000\" aria-pressed=\"false\">5 000</button><button type=\"button\" data-amount=\"7000\" aria-pressed=\"false\">7 000</button><button type=\"button\" data-amount=\"10000\" aria-pressed=\"false\">10 000</button><button type=\"button\" data-amount=\"20000\" aria-pressed=\"false\">20 000</button><button type=\"button\" data-amount=\"50000\" aria-pressed=\"false\">50 000</button></div>", updated, count=1, flags=re.S)
                if (rate_count, preset_count) != (1, 1):
                    raise RuntimeError("Unexpected calculator markup.")
            if updated != current:
                files.append((name, updated.encode("utf-8")))
        if len(files) == 1 and exists(sftp, posixpath.join(public_root, logo_path)):
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
