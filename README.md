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

## Pięć nowych kierunków (11–15)

`/nowe-wersje/` zawiera porównanie pięciu niezależnych propozycji:

- `/wersja-11/` — Katalog: zielono-biały układ oferty z przełączaniem kategorii.
- `/wersja-12/` — Gazeta: redakcyjna kompozycja, szeryfowa typografia i zdjęcie punktu.
- `/wersja-13/` — Orbita: fioletowa scena z produktami i wyborem ścieżki sprzedaży lub zakupu.
- `/wersja-14/` — Warsztat: techniczny układ, pomarańczowe akcenty i proces obsługi.
- `/wersja-15/` — Studio: boczna nawigacja, magentowy akcent i przesuwana galeria kategorii.

Wszystkie propozycje zachowują oryginalne logo i prowadzą do istniejących podstron usług. Dotychczasowe wersje i strona główna pozostają dostępne. Test `npm run test:variants` obejmuje 15 propozycji, trzy strony porównania, 72 kombinacje rozmiarów ekranu i interakcje nowych projektów.

## Nowa seria 16–20

`/swieze-wersje/` porównuje pięć nowych projektów pod osobnymi adresami:

- `/wersja-16/` — Punkt: biel, czerwień, duża typografia i pozioma kompozycja fotografii.
- `/wersja-17/` — Obieg: wybór jednego z czterech celów zmienia zdjęcie, opis i dalszą ścieżkę; limonkowy akcent.
- `/wersja-18/` — Konkretnie: ultramarynowy akcent i duży rozwijany indeks usług.
- `/wersja-19/` — Na miejscu: pomarańczowy akcent i prawdziwa fotografia punktu z informacją o dojeździe.
- `/wersja-20/` — Drugi ruch: typograficzna kompozycja z produktami i magentowym akcentem.

Projekty używają własnych układów i osobnego arkusza stylów `src/next-variants.css`. Oryginalne logo, dane kontaktowe i istniejące podstrony pozostają dostępne. Fonty Inter Tight i Space Grotesk są serwowane lokalnie. Menu mobilne obsługuje klawiaturę i Escape; animacje respektują ograniczenie ruchu. Główna pod `/` pozostaje bez zmian.

`npm run test:next` sprawdza 24 kombinacje strony i szerokości, cztery stany wyboru celu, menu mobilne, klawiaturę, linki usług, akordeon, obrazy i zachowanie obecnej głównej.

W tej sesji próby odczytu Awwwards, Godly i Land-book zostały zablokowane przez proxy (403); nie deklarujemy przejrzenia ich bieżących realizacji ani nie przypisujemy projektom niezweryfikowanych inspiracji. Zdjęcia punktu są oryginalnymi plikami źródłowymi o ograniczonej rozdzielczości (500 px).

## Pracownia — nowe propozycje 21–25

`/pracownia-wersje/` porównuje pięć autorskich stron pod nowymi adresami:

- `/wersja-21/` — Własny kierunek: plakat i przewodnik z kopiowaniem listy przed wizytą.
- `/wersja-22/` — Rzeczy z historią: redakcyjna prezentacja przedmiotu i kontekstowe działania.
- `/wersja-23/` — Jasny rachunek: kalkulator 2,5% / 15 dni i 5% / 30 dni. Wynik jest orientacyjny; informacja o umowie na 31 dni i potwierdzeniu warunków jest widoczna przy kalkulatorze.
- `/wersja-24/` — Tu, na Pocztowej: prawdziwe zdjęcie gablot i planer wizyty według dnia oraz sposobu dojazdu.
- `/wersja-25/` — Działaj dalej: nawigacja zadaniowa i przygotowanie do rozmowy z serwisem według objawu usterki.

Nowa seria zachowuje oryginalne logo, dane i podstrony. Nie zmienia głównej ani propozycji 1–20. Klasy nowych kompozycji mają osobne prefiksy. Żadne z narzędzi nie wysyła danych. Zdjęcia kategorii nie stanowią deklaracji dostępności produktów. Podglądy na stronie porównania są zrzutami działających stron, a każdy prowadzi do pełnego projektu.

Punkty odniesienia: [Bulletproof](https://www.awwwards.com/sites/bulletproof) — wyrazistość marki; [SANTAL](https://www.awwwards.com/sites/santal) — architektoniczny porządek; [Grids](https://www.awwwards.com/sites/grids-1) — eksperymenty z siatką. Odczytano karty Awwwards; serwer obrazów odmówił dostępu, więc nie weryfikowano ich wizualnych detali. Godly i Land-book również odmówiły dostępu. Projekty nie kopiują realizacji.

`npm run test:lab` sprawdza pięć stron, 20 kombinacji szerokości, obrazy, menu mobilne, klawiaturę, przejścia do usług i działanie pięciu narzędzi. Generuje również podglądy JPEG w `public/previews/` oraz zrzuty całych stron w `/tmp/sezam-lab-*.png`. Po wygenerowaniu podglądów ponów build przed publikacją. Zmienna `TEST_URL` i `CHROMIUM_PATH` działają jak w pozostałych testach.

## Wersja 26 — Dobry ruch

`/wersja-26/` jest osobną propozycją o miękkiej kompozycji bento, zaokrąglonych panelach, warstwowych zdjęciach, subtelnych cieniach i animacji respektującej ograniczenie ruchu. Wybór celu zmienia opis i ścieżkę usługi; natywny dialog pomaga przygotować się do wizyty. Zachowano oryginalne logo, dane kontaktowe i podstrony. Nowy moduł `src/soft26.js` i style `src/soft26.css` nie zmieniają dotychczasowych propozycji.

Przejrzano karty ThemeForest: [Frameloft](https://themeforest.net/item/frameloft-creative-agency-photography-react-template/65651542) (bento i interaktywne sekcje) oraz [Cashelrie](https://themeforest.net/item/cashelrie-pawn-shop-wordpress-theme/21837720) (kontekst branżowy). Karty odczytano przez wyszukiwanie; bezpośredni dostęp ze środowiska był blokowany. Implementacja jest autorska, bez użycia płatnego kodu lub zasobów szablonów.

Weryfikacja wersji 26: build, zrzuty desktop/mobile, szerokości 320/390/768/1440 px, obrazy, cztery stany wyboru celu, cztery warianty przewodnika, dialog i Escape, mobilne menu, przejście do serwisu oraz zachowanie głównej.

## Wersja 27 — centrum możliwości

`/wersja-27/` to osobny projekt o strukturze serwisu handlowego: menu rozwijane z kategoriami, ręcznie przełączany baner fotograficzny, kalkulator i suwak kwoty, osiem kategorii z wyszukiwaniem i filtrami, panel szczegółów, porównanie ścieżek usług dla 2–3 kategorii, cztery instrukcje procesu, powiększenie wnętrza oraz panel kontaktu. Porównanie dotyczy usług, nie dostępności produktów ani ich cen. Kalkulator zachowuje stawki lombardgorzow.com: 15 dni / 2,5% oraz 30 dni / 5%, z informacją o umowie na 31 dni i potwierdzeniu warunków w punkcie.

Przed projektowaniem odczytano https://sezamgold.pl/beta/ i https://sezam.com.pl/beta/ przez narzędzie WWW, a następnie odtworzono lokalnie i obejrzano ich źródła z repozytoriów właściciela `angsm111-dot/sezamgold` oraz `angsm111-dot/sezam.com.pl` (`dist/w1/`). Bezpośredni dostęp HTTP ze środowiska był blokowany. Kategorie fotograficzne, zdjęcie pierścionków, wnętrze i grafiki przedmiotów pochodzą z tych projektów Sezamu; kopie zoptymalizowano w `public/images/portal27/`. Nie zmieniano repozytoriów źródłowych ani bet na hostingu. Dodatkowy punkt odniesienia dla struktury usług: https://www.cashconverters.co.uk/.

`npm run test:portal` sprawdza pięć szerokości 320–1440 px, obrazy, menu, trzy tematy banera, kalkulator i suwak, wyszukiwanie z pustym wynikiem, filtry, panele kategorii, limit i tabelę porównania, cztery procesy, galerię, panel kontaktowy, mobilną nawigację i zachowanie głównej oraz wersji 26. Zrzuty są w `/tmp/sezam27-*.png`.

## Wersja 28 — interaktywna witryna

`/wersja-28/` przedstawia autorską przestrzenną ekspozycję: centralny przedmiot na podium, drugi plan, cztery kategorie przełączane przyciskami i strzałkami, hotspot z przygotowaniem przedmiotu, cztery cele wizyty zmieniające treść i akcent kolorystyczny. Nie korzysta z układu źródeł beta ani ze struktury wersji 27. Zdjęcia kategorii pochodzą z istniejących zasobów Sezamu.

Wybory z ekspozycji synchronizują się z „Moim planem”: celem i przedmiotem wizyty, wskazówkami, checklistą i paskiem postępu. Zmiana wyboru zeruje przygotowania; plan można skopiować do schowka. Wybór naprawy ustawia telefon, a przejście do innego przedmiotu wraca do zastawu. Dla sprzedaży telefonu i laptopa link kieruje do elektroniki. Plan działa lokalnie, bez wysyłania danych i bez fikcyjnej rezerwacji. Ruch i paralaksa respektują `prefers-reduced-motion`.

`npm run test:showroom` sprawdza pięć szerokości 320–1440 px, obrazy, cztery cele i przedmioty, strzałki, hotspot, synchronizację planu, checklistę, postęp i reset, rzeczywistą zawartość schowka, zdjęcie w dialogu, mobilne menu, Escape i przejście do serwisu. Zrzuty są w `/tmp/sezam28-*.png`. Pozostałe propozycje i główna pozostają dostępne.

## Wersje 29 i 30 — jasny i ciemny kierunek

`/wersja-29/` rozwija charakter jasnej referencji użytkownika: ciepłe światło, delikatny punktowy wzór, wyraźna oferta, pomarańczowe działania i boczny panel z rzeczowymi informacjami. `/wersja-30/` ma osobną, centralną kompozycję w ciemnej tonacji, złote działania, kontakt przez WhatsApp oraz pas faktów o punkcie. Oba projekty zachowują oryginalne logo, bez kopiowania układu i treści ze zrzutów. Nie przeniesiono niezweryfikowanych liczb klientów, ocen, czasu obsługi ani twierdzeń o najniższej cenie.

Działają: kalkulator 2,5% / 15 dni i 5% / 30 dni według lombardgorzow.com (z informacją o umowie 31-dniowej), suwak kwoty, wybór kategorii, pytania rozwijane i menu mobilne. Wersje mają wzajemne odnośniki. `npm run test:duo` sprawdza dwa adresy, osiem kombinacji szerokości, obrazy, kalkulator, błędne dane, suwak, trzy kategorie, FAQ, menu, Escape i przejście do serwisu. Zrzuty: `/tmp/sezam-duo-*.png`.

## Wersja 31 — szarości i złoto

`/wersja-31/` zachowuje centralną kompozycję ciemnej wersji 30 w jasnej, chłodnej palecie: białe powierzchnie, perłowe szarości, grafitowa typografia, stonowane szczotkowane złoto, delikatne obramowania i cienie. Ciemna wersja 30 pozostaje dostępna. Sprawdzono 320/390/768/1440 px, obrazy, kalkulator, przełączanie kategorii, menu mobilne i Escape. Zrzuty: `/tmp/sezam31-*.png`.

### Rozwinięcie wersji 31 — metaliczne powierzchnie i nawigacja

Dodano chłodne gradienty szarości i srebra w tle, pasie faktów, kartach, kalkulatorze i sekcji kontaktowej; złote gradienty tytułu, przycisków i ikon; krawędzie ze światłem i warstwowe cienie. Złote wypełnienia pod białymi napisami są ciemniejsze dla czytelności. Przyciski mają przejście świetlne po najechaniu, karty unoszą się, a menu łagodnie się rozwija. Ruch jest ograniczany przez `prefers-reduced-motion`.

Nawigacja wersji 31: przyklejony pasek, kapsułowe skróty do sekcji z oznaczeniem oglądanej sekcji, rozwijane menu z opisami usług i kontaktem telefonicznym, zamykanie przez Escape i kliknięcie poza menu. Wersje 29 i 30 zachowują dotychczasowy układ. `npm run test:silver` sprawdza 5 szerokości, widoczność przycisku menu także przy 320 px, przejście do kalkulatora, kalkulację, kategorie, menu mobilne, Escape, kliknięcie poza menu i przejście do usługi. Zrzuty: `/tmp/sezam31-polish-*.png`.

### Odciążenie wersji 31

Usunięto duże metaliczne gradienty i ciemnozłote napisy. Tło jest białe, nagłówki grafitowe i szaroniebieskie, główne przyciski grafitowe. Jasne szampańskie złoto zostało w ikonach i krótkiej linii pod tytułem. Uproszczono powierzchnie kart, kalkulatora i menu; ograniczono cienie, rozjaśniono obramowania i dodano przestrzeń. Zachowano funkcje i sprawdzenie `test:silver` dla pięciu szerokości. Czytelne teksty informacyjne mają ciemniejszy odcień szarości od dekoracyjnych detali.

## Wersja 32 — fotografia i cztery sprawy

`/wersja-32/` to nowa kompozycja: duża fotografia po lewej, cztery rozwijane ścieżki usług po prawej i poziomy kalkulator pod pierwszym ekranem. Wybór usługi zmienia zdjęcie, szczegóły i trzy wskazówki „Przed wizytą”. Instrukcje można również przełączać bez powrotu do góry. Jasna, oszczędna paleta: biel, chłodne szarości, grafit i złoto tylko w drobnych detalach. Zdjęcia pochodzą z zasobów Sezamu; nie reprezentują aktualnego stanu magazynowego. Nowe pliki: `src/concept32.js`, `src/concept32.css`, `public/images/concept32/`.

Sprawdzono build, 320/390/768/1024/1440 px, obrazy, cztery panele i zdjęcia, synchronizację wskazówek, kalkulator obu okresów i błędne kwoty, mobilne menu, Escape i przejście do serwisu. Zrzuty: `/tmp/sezam32-*.png`. Starsze propozycje zachowano.

## Wszystkie projekty w jednym miejscu

`/wszystkie-wersje/` to interaktywny przełącznik 37 propozycji i obecnej głównej. Jedna ramka ładuje tylko wybrany projekt. Lista ma wyszukiwanie po numerze lub nazwie, a podgląd oferuje szerokości 1440 px (komputer) i 390 px (telefon), skalowane do dostępnego miejsca. Można przewijać stronę i sprawdzać jej interakcje, przejść strzałkami do sąsiedniego projektu, zresetować podgląd oraz otworzyć wersję osobno.

Parametry `?wersja=31&widok=telefon` zachowują wybór w linku. Bez parametrów otwiera się najnowsza propozycja. Na telefonie lista projektów otwiera się przyciskiem. `npm run test:all-versions` sprawdza załadowanie wszystkich 38 projektów, nagłówki, linki, zaznaczenie, przełączanie szerokości, strzałki i granice, wyszukiwanie, pusty wynik, cztery rozmiary ekranu, mobilną listę, Escape oraz zachowanie wyboru po odświeżeniu. Zrzuty: `/tmp/sezam-all-*.png`.


## Wersje 33–37 — pięć niezależnych kompozycji

Nowe układy zaprojektowano bez wzorowania się na układach stron Sezamu. Z istniejącego projektu wykorzystano treści, logo, dane kontaktowe i zdjęcia przedmiotów. Główna i wersje 1–32 pozostają dostępne.

- `/wersja-33/` — Mapa spraw: ilustracyjna mapa usług i aktualizowany panel przygotowania do wizyty.
- `/wersja-34/` — Bilet do Sezamu: wybór potrzeby i przedmiotu tworzy listę na wizytę, którą można skopiować.
- `/wersja-35/` — Porozmawiajmy: krótki przewodnik prowadzi od potrzeby przez przedmiot do właściwej usługi, z cofaniem i restartem.
- `/wersja-36/` — Cztery drzwi: rozwijane panele pokazują usługę i jej trzy następne kroki.
- `/wersja-37/` — Przedmiot × potrzeba: interaktywna tabela dobiera usługę do przedmiotu i zamiaru klienta.

Nie dodano fikcyjnych wycen, rezerwacji ani dostępności produktów. Mapa jest oznaczona jako schemat; rzeczywisty dojazd otwiera Mapy Google. Przewodnik działa lokalnie, bez pozornego AI i wysyłania danych.

`npm run test:new-five` sprawdza 20 zestawień strony i szerokości (320, 390, 768, 1440 px), obrazy, menu i Escape oraz najważniejsze interakcje wszystkich pięciu wersji, w tym kopiowanie listy do schowka. Przełącznik obejmuje teraz 37 propozycji oraz obecną główną. Weryfikacja wizualna: komputer i telefon, zrzuty `/tmp/sezam-new-*.png`.


## Wersja 38 — Nowy obrót

Samodzielny portal handlowy: gęstsza nawigacja, duża fotograficzna mozaika, ekspozycje skupu i serwisu, przewijane kategorie, przegląd możliwości oraz zdjęcie rzeczywistego punktu. Paleta śliwki, kremu i złota, warstwowe fotografie i mocniejsza typografia zastępują oszczędne układy wcześniejszych wersji. Mobilny pasek oferuje telefon, dojazd, kategorie i prawdziwe ogłoszenia OLX. Nie dodano fikcyjnych produktów ani cen.

Wyszukiwanie rozpoznaje kategorie i intencje usługowe, a dla nieznanego hasła wyświetla wyjaśnienie i telefon. Kategorie aktualizują zdjęcie, opis i właściwą ścieżkę usługi. Zachowano starsze wersje, a przełącznik obejmuje 38 propozycji i obecną główną.

Próby dostępu do lombard-slonce.pl, Allegro i Back Market zostały zablokowane przez środowisko; nie oparto projektu na nieobejrzanych widokach. `npm run test:market`: pięć szerokości 320–1440 px, obrazy, kategorie, wyszukiwarka i brak wyników, mobilne menu, Escape, FAQ i integracja przełącznika. Weryfikacja wizualna: `/tmp/sezam38-390.png` i `/tmp/sezam38-1440.png`.


## Wersje 39–43 — pięć niezależnych kierunków materiałowych

Nowe propozycje powstały w osobnym module `src/material-five.js` i `src/material-five.css`. Nie korzystają z rendererów ani kompozycji poprzednich wersji. Zachowano logo, zweryfikowane treści, dane punktu, fotografie i istniejące usługi. `public/images/materials/marble.svg` jest własną, dekoracyjną teksturą marmuru.

- `/wersja-39/` — **Marmurowy salon**: architektoniczna, łukowa kompozycja zdjęć, szeryfowa typografia, mineralna biel i matowe złoto. Przewodnik w modalnym oknie dobiera przygotowanie do rodzaju przedmiotu.
- `/wersja-40/` — **Srebrny pulpit**: boczna nawigacja, zwarta plansza usług, szczotkowane srebro i grafit. Dwa pola dobierają usługę i kroki wizyty; naprawa wymusza telefon. Na mobile nawigacja przechodzi do dolnego paska.
- `/wersja-41/` — **Rzeczy — magazyn**: duży masthead, fotograficzna okładka i asymetryczny skład redakcyjny. Interaktywny indeks przedmiotów pokazuje odpowiednie działania i przygotowanie.
- `/wersja-42/` — **Panorama Sezamu**: fotografia na cały ekran, szklany panel i dolny dok usług. Sceny przełączają jednocześnie zdjęcie, treść, link i kolejne kroki. Bez automatycznego przewijania; dostępne strzałki i klawiatura.
- `/wersja-43/` — **Obiekty w obiegu**: centralny postument ze srebra, ciepła aureola i wielka konturowa typografia. Wybór obiektu otwiera właściwe możliwości sprzedaży, zastawu, zakupu i — wyłącznie dla telefonu — naprawy.

Kontekst inspiracyjny: dostępne strony opisów realizacji Awwwards [Santal](https://www.awwwards.com/sites/santal/), [Delta Cafés](https://www.awwwards.com/sites/delta-cafes/) i [Bulletproof](https://www.awwwards.com/sites/bulletproof/). Kierunki pracy: architektoniczne kadrowanie i materiał, rytm opowiadania o kategorii, odważna skala typografii. Nie kopiowano layoutów. Pliki podglądów Awwwards oraz Godly, Land-book i bezpośrednie strony dodatkowych marek były niedostępne w środowisku; nie deklarujemy ich wizualnego przejrzenia.

`npm run test:materials` sprawdza pięć stron przy szerokościach 320/390/768/1024/1440 px, dekodowanie zdjęć, brak poziomego przepełnienia, menu modalne, fokus i Escape, przygotowanie do wizyty, dobór usługi, indeks, panoramę z zawijaniem i obsługą klawiaturą oraz działania dla obiektów. `npm run test:all-versions` weryfikuje wszystkie 44 strony (43 propozycje i obecna główna) i przełącznik. Weryfikacja wizualna: `/tmp/sezam-material-{39..43}-{390,1440}.png`.
