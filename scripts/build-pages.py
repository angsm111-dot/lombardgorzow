#!/usr/bin/env python3
"""Build the selected SEZAM website from shared layout and page sources."""
from pathlib import Path
from html import escape
from check_frozen_versions import verify
from version_navigation import version_navigation

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site'
PAGES = [
    ('home', '', 'Strona główna', 'SEZAM — Daj rzeczom nową wartość. Lombard Gorzów', 'Lombard SEZAM w Gorzowie Wielkopolskim. Pożyczki pod zastaw, skup złota i srebra, biżuteria i elektronika. Odwiedź nas przy Pocztowej 11.'),
    ('home-current', 'wersja-obecna', 'Obecna wersja strony głównej', 'SEZAM — obecna, skrócona strona główna', 'Zachowana skrócona wersja strony głównej SEZAM z odnośnikami do osobnych podstron.'),
    ('oferta', 'oferta', 'Nasza oferta', 'Nasza oferta — skup, zastaw, sprzedaż i serwis | SEZAM Gorzów', 'Sprawdź ofertę SEZAM: skup złota i elektroniki, pożyczki pod zastaw, sprzedaż biżuterii oraz serwis telefonów w Gorzowie.'),
    ('co-przyjmujemy', 'co-przyjmujemy', 'Co przyjmujemy', 'Co przyjmujemy pod zastaw? | Lombard SEZAM Gorzów', 'Złoto, srebro, platyna, brylanty, telefony, laptopy, konsole, elektronarzędzia i rowery. Sprawdź, co możesz przynieść do wyceny w Lombardzie SEZAM.'),
    ('cennik-zlota', 'cennik-zlota', 'Cennik złota', 'Cennik skupu złota | SEZAM Gorzów', 'Cennik skupu złota w Lombardzie SEZAM. Sprawdź stawki dla poszczególnych prób i oblicz orientacyjną wartość swojego złota.'),
    ('obraczki', 'obraczki', 'Obrączki', 'Obrączki ślubne | Lombard SEZAM Gorzów', 'Poznaj obrączki ślubne w SEZAM. Obejrzyj kolory, wzory i wykończenia oraz przejdź do katalogu obraczkigorzow.pl.'),
    ('blog', 'blog', 'Blog', 'Blog — porady | Lombard Gorzów SEZAM', 'Lombard Gorzów: praktyczne poradniki SEZAM o przygotowaniu do wizyty, wycenie złota, elektronice i wyborze między zastawem a sprzedażą.'),
    ('blog-pierwsza-wizyta', 'blog/pierwsza-wizyta-w-lombardzie', 'Pierwsza wizyta', 'Pierwsza wizyta w lombardzie — jak się przygotować? | Lombard Gorzów SEZAM', 'Sprawdź, co przygotować przed pierwszą wizytą w lombardzie. Praktyczna lista informacji, przedmiotów i pytań do wyceny w SEZAM w Gorzowie.'),
    ('blog-wycena-zlota', 'blog/od-czego-zalezy-wycena-zlota', 'Wycena złota', 'Od czego zależy wycena złotej biżuterii? | Lombard Gorzów SEZAM', 'Próba, masa, stan i rodzaj wyrobu. Zobacz, jakie informacje pomagają przygotować wycenę złotej biżuterii w Lombardzie SEZAM w Gorzowie.'),
    ('blog-elektronika', 'blog/telefon-laptop-przygotowanie-do-wyceny', 'Telefon i laptop', 'Telefon lub laptop — przygotowanie do wyceny | Lombard Gorzów SEZAM', 'Jak przygotować telefon lub laptop do wyceny? Model, stan, akcesoria i ochrona danych przed wizytą w Lombardzie SEZAM w Gorzowie.'),
    ('blog-zastaw-sprzedaz', 'blog/zastaw-czy-sprzedaz-przedmiotu', 'Zastaw czy sprzedaż', 'Zastaw czy sprzedaż przedmiotu? | Lombard Gorzów SEZAM', 'Poznaj praktyczne różnice między zastawem a sprzedażą przedmiotu. Przygotuj pytania i sprawdź możliwości w Lombardzie SEZAM w Gorzowie.'),
    ('kalkulator', 'kalkulator', 'Kalkulator', 'Kalkulator pożyczki pod zastaw | SEZAM Gorzów', 'Oblicz orientacyjny koszt pożyczki pod zastaw w SEZAM. Wybierz kwotę oraz 15 lub 30 dni i zobacz opłatę oraz łączną kwotę do spłaty.'),
    ('o-nas', 'o-nas', 'Poznaj SEZAM', 'Poznaj SEZAM — Lombard Gorzów Wielkopolski', 'Poznaj Lombard SEZAM przy Pocztowej 11 w Gorzowie. Ponad 25 lat doświadczenia, dyskretna obsługa i jasne zasady.'),
    ('pytania', 'pytania', 'Pytania', 'Pytania i odpowiedzi | Lombard SEZAM Gorzów', 'Odpowiedzi na pytania o zastaw, wycenę, skup złota i zakupy w Lombardzie SEZAM w Gorzowie Wielkopolskim.'),
    ('kontakt', 'kontakt', 'Kontakt', 'Kontakt i dojazd — Pocztowa 11 | SEZAM Gorzów', 'Lombard SEZAM, Pocztowa 11, Gorzów Wielkopolski. Telefon 601 775 146, godziny otwarcia, WhatsApp i wskazówki dojazdu.'),
]

def build():
    verify()
    layout = (ROOT / 'src/layout.html').read_text()
    paths = []
    for key, slug, name, title, description in PAGES:
        source = ROOT / f'src/pages/{key}.html'
        if not source.is_file():
            raise SystemExit(f'Missing page source: {source}')
        path = '/' + slug + '/' if slug else '/'
        is_home = key in ('home', 'home-current')
        crumbs = '' if is_home else f'<nav class="breadcrumbs wrap" aria-label="Ścieżka nawigacji"><a href="/">Strona główna</a><span aria-hidden="true">/</span><span aria-current="page">{escape(name)}</span></nav>'
        if slug.startswith('blog/'):
            crumbs = f'<nav class="breadcrumbs wrap" aria-label="Ścieżka nawigacji"><a href="/">Strona główna</a><span aria-hidden="true">/</span><a href="/blog/">Blog</a><span aria-hidden="true">/</span><span aria-current="page">{escape(name)}</span></nav>'
        extra = '<script src="/prices.js" defer></script><link rel="stylesheet" href="/metal-theme.css"><link rel="stylesheet" href="/pricing-layout.css">' if key == 'cennik-zlota' else ('<link rel="preload" as="image" href="/assets/sezam-jewelry-hafner.webp">' if is_home else '')
        if key == 'co-przyjmujemy':
            extra += '<link rel="stylesheet" href="/categories.css">'
        if key == 'obraczki':
            extra += '<link rel="stylesheet" href="/rings.css">'
        if key == 'blog' or key.startswith('blog-'):
            extra += '<link rel="stylesheet" href="/blog.css">'
        if key == 'home-current':
            extra += '\n<meta name="robots" content="noindex,follow">'
        switcher = version_navigation(1 if key == 'home' else 2 if key == 'home-current' else None)
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
        if slug.startswith('blog/'):
            page = page.replace('<a href="/blog/">Blog</a>', '<a href="/blog/" class="active">Blog</a>')
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
