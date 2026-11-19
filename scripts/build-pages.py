#!/usr/bin/env python3
"""Build the selected SEZAM website from shared layout and page sources."""
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site'
PAGES = [
    ('home', '', 'Strona główna', 'SEZAM — Daj rzeczom nową wartość. Lombard Gorzów', 'Lombard SEZAM w Gorzowie Wielkopolskim. Pożyczki pod zastaw, skup złota i srebra, biżuteria i elektronika. Odwiedź nas przy Pocztowej 11.'),
    ('home-current', 'wersja-obecna', 'Obecna wersja strony głównej', 'SEZAM — obecna, skrócona strona główna', 'Zachowana skrócona wersja strony głównej SEZAM z odnośnikami do osobnych podstron.'),
    ('oferta', 'oferta', 'Nasza oferta', 'Nasza oferta — skup, zastaw, sprzedaż i serwis | SEZAM Gorzów', 'Sprawdź ofertę SEZAM: skup złota i elektroniki, pożyczki pod zastaw, sprzedaż biżuterii oraz serwis telefonów w Gorzowie.'),
    ('co-przyjmujemy', 'co-przyjmujemy', 'Co przyjmujemy', 'Co przyjmujemy pod zastaw? | Lombard SEZAM Gorzów', 'Złoto, srebro, platyna, brylanty, telefony, laptopy, konsole, elektronarzędzia i rowery. Sprawdź, co możesz przynieść do wyceny w Lombardzie SEZAM.'),
    ('cennik-zlota', 'cennik-zlota', 'Cennik złota', 'Cennik skupu złota | SEZAM Gorzów', 'Cennik skupu złota w Lombardzie SEZAM. Sprawdź stawki dla poszczególnych prób i oblicz orientacyjną wartość swojego złota.'),
    ('kalkulator', 'kalkulator', 'Kalkulator', 'Kalkulator pożyczki pod zastaw | SEZAM Gorzów', 'Oblicz orientacyjny koszt pożyczki pod zastaw w SEZAM. Wybierz kwotę oraz 15 lub 30 dni i zobacz opłatę oraz łączną kwotę do spłaty.'),
    ('o-nas', 'o-nas', 'Poznaj SEZAM', 'Poznaj SEZAM — Lombard Gorzów Wielkopolski', 'Poznaj Lombard SEZAM przy Pocztowej 11 w Gorzowie. Ponad 25 lat doświadczenia, dyskretna obsługa i jasne zasady.'),
    ('pytania', 'pytania', 'Pytania', 'Pytania i odpowiedzi | Lombard SEZAM Gorzów', 'Odpowiedzi na pytania o zastaw, wycenę, skup złota i zakupy w Lombardzie SEZAM w Gorzowie Wielkopolskim.'),
    ('kontakt', 'kontakt', 'Kontakt', 'Kontakt i dojazd — Pocztowa 11 | SEZAM Gorzów', 'Lombard SEZAM, Pocztowa 11, Gorzów Wielkopolski. Telefon 601 775 146, godziny otwarcia, WhatsApp i wskazówki dojazdu.'),
]

def build():
    layout = (ROOT / 'src/layout.html').read_text()
    paths = []
    for key, slug, name, title, description in PAGES:
        source = ROOT / f'src/pages/{key}.html'
        if not source.is_file():
            raise SystemExit(f'Missing page source: {source}')
        path = '/' + slug + '/' if slug else '/'
        is_home = key in ('home', 'home-current')
        crumbs = '' if is_home else f'<nav class="breadcrumbs wrap" aria-label="Ścieżka nawigacji"><a href="/">Strona główna</a><span aria-hidden="true">/</span><span aria-current="page">{escape(name)}</span></nav>'
        extra = '<script src="/prices.js" defer></script><link rel="stylesheet" href="/metal-theme.css">' if key == 'cennik-zlota' else ('<link rel="preload" as="image" href="/assets/sezam-jewelry.webp">' if is_home else '')
        if key == 'co-przyjmujemy':
            extra += '<link rel="stylesheet" href="/categories.css">'
        if key == 'home-current':
            extra += '\n<meta name="robots" content="noindex,follow">'
        original_active = ' aria-current="page"' if key == 'home' else ''
        current_active = ' aria-current="page"' if key == 'home-current' else ''
        switcher = ('<nav class="version-switcher" aria-label="Porównaj wersje strony głównej"><div class="wrap">'
                    '<span class="version-switcher-label">Porównaj stronę główną</span><div class="version-switcher-links">'
                    f'<a href="/"{original_active}>Pierwsza — pełna</a>'
                    f'<a href="/wersja-obecna/"{current_active}>Obecna — skrócona</a>'
                    '</div></div></nav>')
        content = source.read_text()
        for partial, filename in [('google_reviews', 'google-reviews'), ('new_customer_offer', 'new-customer-offer')]:
            if '{{' + partial + '}}' in content:
                content = content.replace('{{' + partial + '}}', (ROOT / f'src/partials/{filename}.html').read_text())
        values = {'title': escape(title), 'description': escape(description, quote=True), 'canonical': ORIGIN + path,
                  'body_class': 'page-home' if is_home else f'page-subpage page-{key}', 'breadcrumbs': crumbs,
                  'content': content, 'extra_head': extra, 'version_switcher': switcher}
        page = layout
        for token, value in values.items():
            page = page.replace('{{' + token + '}}', value)
        # Active navigation also works before JavaScript loads.
        if slug and not is_home:
            page = page.replace(f'<a href="{path}">{name}</a>', f'<a href="{path}" class="active" aria-current="page">{name}</a>')
        if key == 'home-current':
            page = page.replace('href="/" class="brand"', 'href="/wersja-obecna/" class="brand"')
            page = page.replace('class="brand" href="/"', 'class="brand" href="/wersja-obecna/"')
            page = page.replace('<a href="/">Strona główna</a>', '<a href="/wersja-obecna/">Strona główna</a>')
        destination = ROOT / 'dist' / slug / 'index.html'
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page)
        if key != 'home-current':
            paths.append(path)
    urls = '\n'.join(f'  <url><loc>{ORIGIN}{p}</loc></url>' for p in paths)
    (ROOT / 'dist/sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + '\n</urlset>\n')
    print('Built:', ', '.join(paths), 'and /wersja-obecna/')

if __name__ == '__main__':
    build()
