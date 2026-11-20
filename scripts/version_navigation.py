"""Independent comparison controls; these are outside the original project."""

VERSIONS = (
    ('/', '1. Pełna', 'Wersja 1 — pełna strona z bieżącymi poprawkami'),
    ('/wersja-obecna/', '2. Skrócona', 'Wersja 2 — skrócona strona z bieżącymi poprawkami'),
    ('/porownanie-wersji/pierwotna/', '3. Pierwotna', 'Wersja 3 — niezmieniony pierwszy projekt'),
    ('/wersja-posrednia/', '4. Pośrednia', 'Wersja 4 — pełna strona bez sekcji 03 / Dobrze się znamy'),
    ('/wersja-kalkulator/', '5. Kalkulator', 'Wersja 5 — kalkulator przed trzema kafelkami oferty, bez sekcji 01 i 03'),
)


def version_navigation(active):
    links = ''.join(
        f'<a href="{path}" title="{title}"'
        + (' aria-current="page"' if index == active else '')
        + f'>{label}</a>'
        for index, (path, label, title) in enumerate(VERSIONS, start=1)
    )
    return (
        '<nav class="edition-switcher" aria-label="Porównaj pięć wersji strony">'
        '<div class="edition-switcher-inner"><span class="edition-switcher-label">'
        'Porównaj wersje</span><div class="edition-switcher-links">'
        + links + '</div></div></nav>'
    )
