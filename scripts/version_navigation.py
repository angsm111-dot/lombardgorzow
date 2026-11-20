"""Independent comparison controls; these are outside the original project."""

VERSIONS = (
    ('/', '1. Pełna', 'Wersja 1 — pełna strona z bieżącymi poprawkami'),
    ('/wersja-obecna/', '2. Skrócona', 'Wersja 2 — skrócona strona z bieżącymi poprawkami'),
    ('/wersja-pierwotna/', '3. Pierwotna', 'Wersja 3 — niezmieniony pierwszy projekt'),
)


def version_navigation(active):
    links = ''.join(
        f'<a href="{path}" title="{title}"'
        + (' aria-current="page"' if index == active else '')
        + f'>{label}</a>'
        for index, (path, label, title) in enumerate(VERSIONS, start=1)
    )
    return (
        '<nav class="edition-switcher" aria-label="Porównaj trzy wersje strony">'
        '<div class="edition-switcher-inner"><span class="edition-switcher-label">'
        'Porównaj wersje</span><div class="edition-switcher-links">'
        + links + '</div></div></nav>'
    )
