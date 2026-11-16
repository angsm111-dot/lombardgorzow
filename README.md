# Sezam — nowa odsłona

Wielostronicowa strona Sezamu w Gorzowie: pastelowa paleta, duża typografia, redakcyjny układ, osobne strony zamiast jednej długiej sekcji z kartami.

## Uruchomienie

Node 20.19+, 22.12+ lub 24. Sprawdzono na Node 24.

```sh
npm ci
npm run dev
```

`npm run build` generuje `dist/`. `npm run preview` udostępnia build. `npm test` sprawdza działający preview na porcie 4173. Testy wymagają Chromium z `/usr/bin/chromium` (lub `CHROMIUM_PATH`). `TEST_URL` pozwala testować inny adres, także ścieżkę projektu GitHub Pages.

## Podstrony

Strona główna, `/gotowka/`, `/skup-zlota/`, `/telefony-laptopy/`, `/serwis-gsm/`, `/czesci/`, `/na-sprzedaz/`, `/o-nas/`, `/kontakt/`, `/pytania/`, `/galeria/`, `/blog/`.

Build tworzy fizyczne pliki HTML dla każdej podstrony, więc bezpośrednie adresy działają na statycznym hostingu bez reguł przekierowań. Podstrony używają wspólnej aplikacji JavaScript. Lokalna galeria ma powiększanie zdjęć. Blog zachowuje teksty odczytane z oryginału; wpisy, w których oryginalna strona nie udostępnia treści, prowadzą do źródła.

## GitHub Pages

Workflow `.github/workflows/pages.yml` buduje stronę po pushu do `main` i publikuje ją przez oficjalne akcje GitHub Pages.

W repozytorium wybierz **Settings → Pages → Build and deployment → Source: GitHub Actions**. Jeżeli pierwszy workflow zakończył się przed aktywacją Pages, wybierz **Actions → Publish Sezam to GitHub Pages → Run workflow**.

Adres po udanym wdrożeniu: `https://angsm111-dot.github.io/lombardgorzow/`.

Ręczny build dla tej ścieżki:

```sh
SITE_BASE=/lombardgorzow/ npm run build
SITE_BASE=/lombardgorzow/ npm run preview
```

Na własnej domenie użyj zwykłego `npm run build` (domyślna ścieżka `/`).

## Treść i dane

Źródło: lombardgorzow.com, odczyt 16.11.2026. Zdjęcia przechowywane lokalnie. Zachowano dane kontaktowe, usługi, warunki, FAQ, galerię i wpisy. Oferty sprzedaży prowadzą do istniejącego konta OLX, pełne cenniki monet i sztabek do źródła. Starsze wpisy pozostają w oryginalnym archiwum.

Kalkulator używa stawek działającego kalkulatora Sezamu: 2,5% za 15 dni, 5% za 30 dni. Informacje o umowie 31-dniowej i dodatkowych 7 dniach zachowano w FAQ. Starszej, rozbieżnej tabeli oryginału nie przeniesiono; tabela opłat odpowiada kalkulatorowi.

Cennik złota i srebra jest datowanym odczytem, bez automatycznej aktualizacji. Zachowano także nietypowe wartości źródłowe — firma powinna potwierdzić cennik przed wykorzystaniem jako bieżącej oferty. Połączenie z aktualnym źródłem cen wymaga osobnej integracji.

Brak backendu i fikcyjnych formularzy. Kontakt przez telefon, WhatsApp, Facebook i mapy. Strona nie zbiera danych klientów.

## Weryfikacja

Test sprawdza 12 stron, 48 kombinacji strony i szerokości ekranu (320, 390, 768, 1440 px), kalkulator i błędne dane, cennik i przedziały wagowe, obsługę klawiatury, FAQ, galerię, teksty bloga, menu mobilne, ładowanie obrazów i kotwice. Zrzuty kontrolne trafiają do `/tmp/sezam-v2-*.png`.
