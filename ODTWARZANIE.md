# Kopia obu wersji strony SEZAM — 20.11.2026

To samodzielna kopia projektu „SEZAM — Nowa wartość” ze źródłowego commita `e10746c61cdb2e733f0c45a8ad195aa2eb7684f7`. Zachowuje obie strony główne, wspólne podstrony, przełącznik, zdjęcia, fonty i wcześniejsze koncepcje.

| Wersja | Gotowy plik | Źródło |
| --- | --- | --- |
| Pierwsza, pełna | `dist/index.html` | `src/pages/home.html` |
| Obecna, skrócona | `dist/wersja-obecna/index.html` | `src/pages/home-current.html` |

Podglądy:
- https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site/
- https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site/wersja-obecna/

## Uruchomienie kopii

W katalogu tego projektu:

```sh
python3 scripts/build-pages.py
python3 -m http.server 8000 --directory dist
```

Otwórz `http://localhost:8000/` lub `http://localhost:8000/wersja-obecna/`. Nie otwieraj HTML przez `file://`, ponieważ odnośniki zakładają serwowanie katalogu dist jako katalogu głównego serwera. Do lokalnego podglądu wystarczy Python 3. Cennik wymaga połączenia z istniejącym zewnętrznym źródłem cen; kod i obsługa błędów są zachowane, dane giełdowe nie są zamrożone w kopii.

## Przywrócenie lub zamiana stron głównych

Pełna i skrócona zawartość są przechowywane oddzielnie. Można podmienić źródło jednej strony głównej i przebudować HTML bez zmiany podstron oferty, cennika i kontaktu. Przy zamianie obu wariantów należy również zamienić oznaczenia w przełączniku w `scripts/build-pages.py`. Odtwarzając cały projekt na hostingu, opublikuj zawartość `dist/`.

Ta gałąź jest punktem przywracania. Dalsze prace można prowadzić na nowej gałęzi utworzonej z niej. Główna gałąź repozytorium GitHub i jej wdrożenie nie są zmieniane przez tę kopię.
