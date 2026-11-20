# Odtwarzanie trzech wersji strony SEZAM

Ta gałąź `work/sezam-kontakt-cennik` zawiera rozwijany projekt „SEZAM — Nowa wartość”. Odpowiada źródłowemu commitowi Sites `4ab0305f10d69a92ed81105ac55f45bcadda116e`. Wcześniejsza kopia dwóch wersji pozostaje bez zmian na gałęzi `backup/sezam-dwie-wersje-2026-11-20`.

| Wersja | Adres | Zasada |
| --- | --- | --- |
| 1. Pełna | `/` | Rozwijana strona główna ze wszystkimi sekcjami. |
| 2. Skrócona | `/wersja-obecna/` | Rozwijana skrócona strona główna i wspólne podstrony. |
| 3. Pierwotna | `/wersja-pierwotna/` | Zamrożony pierwszy projekt, bez późniejszych dodatków. |

Podgląd: https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site/ — przełącznik prowadzi do wszystkich trzech wersji.

## Uruchomienie kopii

W katalogu projektu:

```sh
python3 scripts/build-pages.py
python3 -m http.server 8000 --directory dist
```

Otwórz `http://localhost:8000/`, `http://localhost:8000/wersja-obecna/` lub `http://localhost:8000/wersja-pierwotna/`. Do lokalnego podglądu wystarczy Python 3. Serwuj cały katalog `dist/`, ponieważ rozwijane strony używają odnośników od katalogu głównego. Cennik wymaga połączenia z zewnętrznym źródłem bieżących cen; kopia zachowuje kod i obsługę błędów, nie zamraża danych cenowych.

## Ochrona i przywracanie

Wersje 1 i 2 mają źródła `src/pages/home.html` oraz `src/pages/home-current.html`, wspólny układ `src/layout.html` i wspólne podstrony. Kolejne poprawki wprowadzamy w obu tych wersjach.

Wersja 3 pochodzi z commitu `95518111742391729b954dc75710b88cdab8b71a`. Jej 20 oryginalnych plików znajduje się w `dist/wersja-pierwotna/projekt/`; osobna ramka z przełącznikiem nie zmienia oryginalnego projektu. Manifest `config/frozen-versions.json` chroni łącznie 22 pliki. Budowanie sprawdza ich sumy SHA-256 i zatrzymuje się po naruszeniu kopii. Nie zmieniaj plików ani sum wersji 3 bez wyraźnej prośby użytkownika o tę wersję.

Aby odtworzyć projekt na hostingu, opublikuj kompletną zawartość `dist/`, w tym `wersja-pierwotna/`. Szczegółowe zasady zawierają `WERSJE.md` i `AGENTS.md`. Gałąź `main` oraz wcześniejszy backup pozostają osobnymi, niezmienionymi zapisami.
