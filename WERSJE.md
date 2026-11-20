# Trzy wersje strony SEZAM

| Wersja | Adres | Zasada dalszej pracy |
| --- | --- | --- |
| 1. Pełna | https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site/ | Wprowadzamy kolejne poprawki. Pełna strona główna ze wszystkimi sekcjami. |
| 2. Skrócona | https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site/wersja-obecna/ | Wprowadzamy te same poprawki. Skrócona strona główna i osobne podstrony. |
| 3. Pierwotna | https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site/wersja-pierwotna/ | Niezmieniony pierwszy projekt do porównania. |

Wersja 3 pochodzi z zachowanego projektu w odcieniu szampańskiego złota, z commitu `95518111742391729b954dc75710b88cdab8b71a`. Wszystkie 20 plików projektu są identyczne z tym zapisem. Oryginalna strona znajduje się w `dist/wersja-pierwotna/projekt/`; przełącznik wersji jest osobną ramką i nie zmienia jej kodu.

Wersja 3 nie zawiera późniejszych dodatków: sztabki i monety na zdjęciu, świątecznego logo i śniegu, nowego banera promocji, nowych przycisków WhatsApp ani nowej nawigacji wielostronicowej. W wersjach 1 i 2 pozostają dotychczasowe poprawki, a na zdjęciu pojawia się wyższa, cieńsza sztabka o fakturze wzorowanej na C.HAFNER.

## Ochrona i odtwarzanie

`config/frozen-versions.json` zawiera sumy SHA-256 oryginalnego projektu oraz jego osobnej ramki. Polecenie `python3 scripts/build-pages.py` sprawdza ich zgodność przed każdym generowaniem bieżących stron. Zmiana lub brak chronionego pliku zatrzymuje budowanie.

Do odtworzenia oryginału z tego repozytorium wystarczy zachować katalog `dist/wersja-pierwotna/` wraz z jego plikami. Kopia całego projektu w GitHubie znajduje się na gałęzi `work/sezam-kontakt-cennik` repozytorium `angsm111-dot/lombardgorzow`. Wcześniejsza kopia dwóch wersji nadal pozostaje na gałęzi `backup/sezam-dwie-wersje-2026-11-20`.

Pliki źródłowe rozwijanych stron to `src/pages/home.html` oraz `src/pages/home-current.html`. Ich wspólny układ jest w `src/layout.html`. Wersji 3 nie generujemy z tego układu.
