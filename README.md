# Sezam — nowa odsłona

Wielostronicowa strona Sezamu w Gorzowie: jasne neutralne tło, oszczędny terakotowy akcent, lokalne fonty Outfit i Manrope, zaokrąglone bryły, przestrzenna prezentacja przedmiotów, animacje przy przewijaniu i interaktywne kategorie. Zachowano podstrony i dane biznesowe.

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

Test sprawdza 12 stron, 48 kombinacji strony i szerokości ekranu (320, 390, 768, 1440 px), kalkulator i błędne dane, cennik i przedziały wagowe, obsługę klawiatury, FAQ, galerię, teksty bloga, menu mobilne, ładowanie obrazów i kotwice. Zrzuty kontrolne trafiają do `/tmp/sezam-v3-*.png`.

## Kierunek wizualny

Aktualna wersja: ciepłoszare tło, białe powierzchnie, wyraźny granatowy tekst, ceglasty akcent i kontrastowe stany wyboru. Zachowano warstwowe kompozycje, zaokrąglenia i animacje.

Przejrzane inspiracje: [Cruip Simple](https://github.com/cruip/tailwind-landing-page-template) (świetlne tła, warstwy, animacje wejścia) i [Shadcn Landing Page](https://github.com/leoMirandaa/shadcn-landing-page) (pływające elementy, głębia, zaokrąglenia). Nie skopiowano szablonu ani jego treści. Kompozycje i implementacja są własne, z zachowaniem zdjęć i danych Sezamu.

Fonty serwowane są lokalnie z pakietów Fontsource. Animacje, ruch perspektywiczny i przewijanie respektują `prefers-reduced-motion`. Przełącznik prezentacji na głównej zmienia kategorię zdjęć, a filtr na stronie sprzedaży zawęża widoczne kategorie. Bez automatycznie przesuwającej się karuzeli.

## Logo i podział treści

Oryginalne logo Sezamu pobrano z `https://lombardgorzow.com/wp-content/uploads/2018/03/SezamLombard_logoRGB-x2.png` i zapisano bez zmian w `public/images/sezam-logo-original.png`. Nagłówek oraz stopka używają tego pliku.

Strona główna zawiera wprowadzenie i skróty usług. Rozwinięcie oferty znajduje się w „Na sprzedaż”, opis kroków w „Gotówka i kalkulator”, opis firmy w „O nas”, FAQ na własnej stronie, a większy blok kontaktu na stronie kontaktowej. Menu zawiera bezpośrednie strony Start, Na sprzedaż, Kontakt oraz rozwijane grupy Usługi i O Sezamie. Wszystkie 12 stron jest dostępnych z nawigacji również na telefonie.

## Pięć wersji głównej do porównania

`/wersje/` otwiera stronę porównania z żywymi miniaturami i odnośnikami do propozycji:

1. `/wersja-1/` — Atelier: butikowa kompozycja, bordowy akcent, szeryfowe nagłówki.
2. `/wersja-2/` — Impuls: kobalt i żółty, mocna typografia i geometryczna kompozycja.
3. `/wersja-3/` — Flow: jasny interfejs z działającym kalkulatorem opłaty.
4. `/wersja-4/` — Po sąsiedzku: zdjęcia punktu, lokalny charakter i ciepła czerwień.
5. `/wersja-5/` — Forma: graficzna typografia, trzy kategorie produktów i akordeon usług.

Wersje są dodatkowymi propozycjami głównej. Obecna strona pod `/` zachowuje swój układ. Wspólne podstrony usług pozostają funkcjonalne. Pasek porównania pozwala przełączać propozycje i wrócić do obecnej strony. Parametr `?preview=1` ukrywa pasek w miniaturach.

`npm run test:variants` sprawdza pięć propozycji, stronę porównania, 24 kombinacje rozmiaru ekranu, obrazy, przejścia do usług, przełączanie wersji, kalkulator Flow, akordeon Forma oraz zachowanie dotychczasowej głównej. Używa tej samej konfiguracji `TEST_URL` i Chromium co `npm test`.

## Dodatkowe wersje inspirowane Impulsem (nr 2)

`/impuls-wersje/` porównuje pięć kolejnych kierunków. Dotychczasowe propozycje pozostają pod swoimi adresami.

- `/wersja-6/` — Impuls Sprint: żółty plakat, centralny nagłówek i trzy kategorie produktów.
- `/wersja-7/` — Impuls Metro: kobaltowy hero i panel szybkiego wyboru usługi.
- `/wersja-8/` — Impuls Pop: pomarańczowy hero, biżuteria w organicznej formie i granatowo-żółte bloki.
- `/wersja-9/` — Impuls Grid: jasna kompozycja, duża typografia i mozaika usług.
- `/wersja-10/` — Impuls Plakat: kobaltowy plakat i kolaż zdjęć punktu.

Nowa strona porównania zawiera odnośnik do oryginalnej wersji nr 2. Pasek przełączania działa osobno dla rodzin 1–5 i 6–10. Test `npm run test:variants` obejmuje teraz 10 wersji, dwie strony porównania i 48 kombinacji rozmiarów ekranu.
