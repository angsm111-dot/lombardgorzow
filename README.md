# SEZAM — nowa wartość

Autorska, responsywna strona informacyjna. Aktualny wariant luksusowy: perłowe szarości, grafit, złoto, srebro i marmurowe powierzchnie. Jasne zdjęcia na kamiennych podestach oraz szeryfowe nagłówki.

## Uruchomienie
Statyczna zawartość znajduje się w `dist/`. Serwuj katalog dowolnym serwerem HTTP. Brak zależności JavaScript. Po zmianach w `src/` uruchom `python3 scripts/build-pages.py`. Generator tworzy strony w `dist/` ze wspólnego szablonu.

## Działające elementy
- Cztery zakładki usług z obsługą klawiatury.
- Kalkulator: 50–100 000 zł; domyślnie 2 000 zł i 15 dni. Stawki 2,5% za 15 dni oraz 5% za 30 dni, zgodne z tabelą źródłową. Walidacja kwoty.
- Podgląd szczegółów monet, sztabek i biżuterii.
- Formularz przygotowujący wiadomość w WhatsApp; niczego sam nie wysyła ani nie zapisuje.
- Godziny według grafiku w strefie Europe/Warsaw, z informacją o potwierdzeniu godzin świątecznych.
- Menu mobilne, FAQ, telefon, linki do cennika i dojazdu.

## Źródła treści
Sprawdzone 16.11.2026:
- https://sezam.com.pl/
- https://sezam.com.pl/kalkulator-oplat/
- https://sezam.com.pl/contact-us-3/
- https://sezam.com.pl/skup-sprzedaz-zlota/
- https://sezam.com.pl/pozyczki-pod-zastaw/
- https://sezam.com.pl/skup-sprzedaz-telefonow/
- https://sezam.com.pl/serwis-telefonow-komorkowych/
- https://sezam.com.pl/faq/
- https://sezam.com.pl/oferta-olx-allegro/

Źródło używa 31 dni w FAQ i 30 dni w tabeli kalkulatora. Nowy kalkulator wiernie stosuje tabelę 15/30 dni i zawiera informację o potwierdzeniu warunków w punkcie. Ceny metali na nowej podstronie `/cennik-zlota/` są pobierane na żywo z tego samego publicznego feedu co sezam.com.pl. Informację „ponad 300 opinii w Google” dodano 20.11.2026 na podstawie danych przekazanych przez właściciela. Nie deklarujemy oceny gwiazdkowej.

## Grafiki
Wbudowane ImageGen, grafiki aranżacyjne, nie katalog konkretnych produktów:
- `dist/assets/sezam-jewelry.webp`: photorealistic yellow gold wedding bands, solitaire ring and chain on a cool white-gray stone circular plinth, soft window light, architectural arch, no text or logos.
- `dist/assets/sezam-tech.webp`: graphite and silver smartphones with a silver laptop on a pale marble circular plinth, cool white architectural studio, no navy, no text or logos.
Odrzucone zdjęcie kobaltowe nie jest częścią strony.

## Sprawdzenie
- Przegląd desktop 1363 px i mobilnego viewportu 390 px (375 px treści po odjęciu przewijania).
- Brak przewijania poziomego, wszystkie obrazy załadowane.
- 5 000 zł / 30 dni = 250 zł opłaty, 5 250 zł łącznie.
- 10 000 zł / 30 dni = 500 zł opłaty, 10 500 zł łącznie.
- 2 000 zł / 15 dni = 50 zł opłaty, 2 050 zł łącznie.
- Kwota 100 001 zł wyświetla błąd i wyłącza kontakt z nieprawidłowym wynikiem.
- Sprawdzono przełączanie oferty, FAQ, modal szczegółów, przejście do formularza i zamykanie menu mobilnego.
- Nie wysyłano wiadomości do firmy podczas testów.

## Poprzednia aktualizacja pastelowa (zachowana w historii Git)
- Dokładny kolor ze strony https://sezamgold.pl/beta/: `--plum: #85275f`, ciemny wariant `#632047` (odczyt stylów przeglądarki 16.11.2026).
- Kafelki usług: lawenda, mięta, róż, błękit; karty produktowe: pastelowe złoto, mięta, lawenda.
- Kolor panelu zmienia się z usługą; pastelowy kalkulator, sekcja doświadczenia i kontakt.
- Zdjęcia produktów pochodzą z publicznej strony SEZAM GOLD: `krugerrand-cutout.webp`, `gold-bars-cutout.webp`, `jewelry-cutout.webp`, pobrane do lokalnych assets.
- Zdjęcie biżuterii na jasnym podeście zachowane w hero.

## Aktualizacja luksusowa — 16.11.2026
- Perłowe szarości i grafit z akcentami złota `#8a7047` oraz srebra `#d9dcde`.
- Marmurowe tła, metaliczne przyciski, cienkie ramki i prostokątne kafelki.
- Nagłówki P052 / URW Base35, lokalne pliki WOFF i dołączona licencja.
- Nowa tekstura `assets/pearl-marble.webp` wygenerowana w ImageGen: jasny marmur z delikatnymi szarymi i złotymi żyłkami.
- Układ komponentów wydzielony w `components.css`, aktualne wykończenie w `luxury.css`.
- Zachowane zdjęcie biżuterii na kamiennym podeście i wszystkie funkcje strony.
- Ponownie sprawdzono desktop 1363 px i mobilną szerokość 375 px, brak poziomego przewijania, przełączanie oferty, modal sztabek oraz kalkulator 5 000 zł / 30 dni = 250 zł opłaty, 5 250 zł łącznie.
- Podgląd zatwierdzonego wyglądu: `docs/sezam-luxury-preview.jpg`.

### Mocniejsze złoto
Na prośbę użytkownika nasycono metaliczne złote gradienty i dopasowano złote napisy, logo, linie, obramowania oraz aktywne elementy do jednej cieplejszej palety. Przegląd wizualny wykonano w podglądzie przeglądarki.

### Korekta złota szampańskiego
Po uwadze o zbyt żółtym kolorze obniżono nasycenie złotych akcentów, zachowując metaliczny połysk. Gradienty, litery, ikony, linie i obramowania mają teraz spójny szampański odcień.

## Porównanie czterech ostatnich wersji
Strona `/porownanie/` prezentuje cztery dokładne kopie opublikowanych wersji: pastelową, klasyczne złoto, mocne złoto i szampańskie złoto. Mapowanie do commitów znajduje się w `dist/porownanie/versions.json`. Strona główna pozostaje w aktualnej wersji szampańskiej.

Porównanie obejmuje siatkę 2×2, powiększenie wybranej wersji, widoki komputer/telefon, wspólne przejście do sekcji, synchronizację przewijania i otwieranie każdej wersji osobno. Podglądy zachowują działające menu, formularze i kalkulatory.

Sprawdzono wszystkie cztery załadowane podglądy, przejście do kalkulatora, wspólne przewijanie, powiększenie, przełączanie urządzenia z zachowaniem sekcji oraz brak poziomego przewijania strony porównania przy szerokości 375 px. Zweryfikowano zgodność wszystkich plików historycznych z commitami i istnienie lokalnych zasobów.


## Cztery nowe koncepcje 05–08 — 16.11.2026
Strona `/koncepcje/` prezentuje cztery odrębne architektury, z oddzielnymi układami i stylami:
- **05 Katalog** (`/koncepcje/katalog/`): wyszukiwarka, boczne filtry, siatka kategorii, ceglasty akcent i pastelowe karty. Wyszukiwanie reaguje na polskie znaki, obsługuje pusty wynik i reset filtrów.
- **06 Atelier** (`/koncepcje/atelier/`): pionowa nawigacja, ciemna galeria z trzema ekspozycjami, duża typografia szeryfowa, oliwkowe i szałwiowe tony.
- **07 Punkt** (`/koncepcje/punkt/`): miętowy pierwszy ekran z wyborem usługi w trzech krokach. Formularz podpowiada następny krok i otwiera przygotowaną wiadomość w WhatsApp; nie wysyła danych samodzielnie.
- **08 Magazyn** (`/koncepcje/magazyn/`): nagłówek w stylu wydawnictwa, kolumny redakcyjne, fotografia na kamieniu, kremowy papier i bordo.

Każdy projekt ma ofertę, kalkulator, historię, pytania i kontakt. HTML generuje `python3 scripts/build-concepts.py`; osobne style każdego projektu pozostają w jego katalogu. Wspólne są wyłącznie elementy bazowe i funkcje (`shared/`), nie konstrukcja strony. Nie dodano fikcyjnych stanów magazynowych ani aktualnych cen.

Nowe porównanie ma układ 2×2, powiększanie, widoki telefonu i komputera, przejście do tego samego tematu oraz opcjonalne wspólne przewijanie. Synchronizacja uwzględnia różną kolejność sekcji. Domyślnie każdą koncepcję przewija się osobno. Zachowano wcześniejsze wersje 01–04 pod `/porownanie/` i dodano przejście między zestawami.

### Inspiracje organizacją treści
Sprawdzono 16.11.2026 treść i strukturę https://www.otomoto.pl/, https://www.mobile.de/, https://allegro.pl/ i https://www.olx.pl/. Obejrzenie układu w przeglądarce było możliwe dla Otomoto i OLX; mobile.de zwróciło Access Denied, Allegro błąd HTTP2. Porównanie wyszukiwania, filtrów, kategorii i ścieżek użytkownika posłużyło do zaprojektowania różnych koncepcji SEZAM; nie kopiowano layoutów ani identyfikacji tych serwisów. Treść usług pochodzi z opisanych wcześniej źródeł SEZAM.

### Weryfikacja nowych koncepcji
- Przejrzano wszystkie pierwsze ekrany na komputerze i telefonie oraz cztery sekcje kalkulatorów.
- Mobilna szerokość każdej strony: 375 px; szerokość dokumentu 375 px, brak poziomego przepełnienia. Wszystkie obrazy załadowane.
- Wyszukiwanie „telefon” zwraca dwie kategorie; zapytanie bez wyników pokazuje stan pusty; reset przywraca sześć kategorii.
- Galeria przechodzi z biżuterii do monet. Modal oferty poprawnie otwiera się i zamyka.
- Wybór usługi „Potrzebuję pożyczki” → „Telefon” pokazuje właściwe zalecenia; reset przywraca nieaktywny przycisk do czasu wyboru.
- Kalkulator: 5000 zł / 30 dni = 250 zł opłaty i 5250 zł łącznie; kwota 0 wyświetla błąd i usuwa odnośnik kontaktowy z nieprawidłowym wynikiem.
- Poprawiono odstępy w tekstach po ukryciu łamań linii i odmianę licznika kategorii.
- Składnia obu skryptów JS, lokalne odnośniki/zasoby i `git diff --check`: bez błędów.
- Podgląd: `docs/sezam-new-concepts-preview.jpg`.


## Pięć odważnych projektów 09–13 — 16.11.2026
Nowy zestaw dostępny pod `/odwazne/`, przygotowany na podstawie trzech załączonych przez użytkownika zrzutów inspiracji (Ticker/Lateral, TopLevel/Tovo, Rocket LMS/Grupo/StoreGo). Przejęto kierunek wizualny — nasycone kolory, ukośne kompozycje, nakładające się panele, światło, głębię i fotografię pełnoekranową. Nie kopiowano cudzych nazw, tekstów, kodu ani identyfikacji.

| Projekt | Układ i charakter | Interakcja |
| --- | --- | --- |
| 09 Pryzmat | Fioletowa scena, neonowy łuk, wyśrodkowany nagłówek, wachlarz trzech barwnych kart | Wybór karty aktywuje ją i wysuwa na pierwszy plan |
| 10 Fala | Turkusowa organiczna przestrzeń, asymetryczna kompozycja ukośnych paneli, jasna strona | Wybór przedmiotu pokazuje wskazówki przed wyceną i odpowiedni odnośnik WhatsApp |
| 11 Noc | Fotografia zegarka na cały ekran, ciemna scenografia i czerwone akcenty, pasek trzech historii | Zmiana historii aktualizuje nagłówek, opis i działanie; zegar pokazuje czas Europe/Warsaw |
| 12 Orbita | Ciemna zieleń, limonkowa typografia, szklane kafle wokół przestrzennego znaku, przesunięte rzędy usług | Cztery usługi na orbicie zmieniają opis i otwierane szczegóły |
| 13 Studio | Koralowo-różowy plakat, duże litery, kolaż produktów, naklejki i pasek tekstu | Filtry Kruszec/Technologia/Wszystko zmieniają widoczne kategorie |

Każdy projekt ma osobny HTML i CSS. Wspólne są podstawowe style, sprawdzone opisy oferty, modal i kalkulator. Generator `python3 scripts/build-bold.py` odtwarza pięć stron. Podgląd `/odwazne/` ma powiększanie, widok komputera/telefonu i wspólne przejście do oferty, kalkulatora oraz kontaktu. Starsze zestawy zachowano, z przejściami między porównaniami.

### Nowe grafiki
Wbudowany ImageGen; aranżacje, nie deklaracja dostępności konkretnych produktów. Zoptymalizowane WebP i używane lokalnie:
- `dist/assets/nocturne-watch.webp` — 1774×887, RGB. Prompt: panoramic cinematic unbranded steel wristwatch on black polished stone, right-side diagonal composition, dark left negative space, crimson and copper rim lighting, sharp metal texture, no text/logos.
- `dist/assets/color-tech.webp` — 1254×1254, RGBA. Prompt: transparent photoreal cutout of generic black phone, open silver laptop and white earbuds, dynamic diagonal composition, turquoise/violet/coral rim lighting, abstract screen wallpaper, individual soft shadows, no text/logos.

### Weryfikacja
- Przejrzano pięć pierwszych ekranów oraz sekcje ofert na komputerze i pięć mobilnych kompozycji.
- Wszystkie mobilne dokumenty mają 375 px szerokości treści i 375 px scrollWidth, wszystkie obrazy załadowane.
- Sprawdzono każdą z pięciu odrębnych interakcji, szczegóły monet i zamykanie modalu.
- Kalkulator: 5000 zł / 30 dni = 250 zł opłaty, 5250 zł łącznie. Wartość 0 pokazuje błąd i usuwa odnośnik z nieprawidłowym wynikiem.
- Sprawdzono powiększenie projektu oraz skok do sekcji w porównaniu.
- Poprawiono mobilną wielkość nagłówka Studio, zastąpiono automatyczne kolorowe emoji kontrolowanymi znakami SVG i odsunięto skrajny kafel Orbity od krawędzi.
- Składnia JS, identyfikatory, kotwice i lokalne ścieżki zasobów oraz `git diff --check` sprawdzone bez błędów. Nie wysyłano wiadomości podczas testów.
- Końcowy podgląd: `docs/sezam-five-bold-preview.jpg`.


## Dziesięć kolejnych projektów 14–23 — 16.11.2026
Nowa galeria `/kolejne/` uzupełnia dotychczasowe zestawy. Każdy projekt ma własny układ HTML i osobny arkusz CSS. Generator `python3 scripts/build-ten.py` odtwarza strony na podstawie współdzielonych, zweryfikowanych elementów treści z `scripts/design_utils.py`.

| Projekt | Kompozycja i sposób przeglądania |
| --- | --- |
| 14 Aurora | Opalizujące pastele, centralna typografia szeryfowa i trzy okrągłe wyspy przedmiotów; wybór kategorii zmienia scenę i główne zdjęcie |
| 15 Mozaika | Asymetryczna ściana barwnych kafli; osobne akcje skupu, elektroniki, biżuterii i kalkulatora |
| 16 Panorama | Trzy fotograficzne panele rozwijane w poziomie; na telefonie układ pionowy |
| 17 Chrom | Srebrno-liliowe studio, duże konturowe litery i karuzela trzech kategorii |
| 18 Rytm | Cztery pełne szerokości pasy typograficzne z rozwijaną treścią: Sprzedaj, Kup, Zastaw, Napraw |
| 19 Ogrody | Album z przechylonym zdjęciem, taśmą, okrągłym kadrem i naturalnymi odcieniami oliwki oraz terakoty |
| 20 Impuls | Limonkowa fotografia, duży plakatowy nagłówek i dolny panel wyboru usługi |
| 21 Aksamit | Bordowo-różowa fotografia biżuterii, wielka typografia szeryfowa i kartka z zaproszeniem |
| 22 Sygnał | Interaktywny wybór tematu w kompozycji rozmowy; lokalne odpowiedzi i przejście do konkretnej usługi |
| 23 Horyzont | Monumentalny napis wypełniony fotografią złota, szeroki kadr i poziomy indeks usług |

Porównanie pozwala obejrzeć wszystkie projekty, powiększyć jeden, wybrać komputer/telefon, przejść wspólnie do oferty lub kontaktu oraz zsynchronizować przewijanie. Kalkulator w każdej wersji otwiera się w oknie. Zachowano wcześniejsze serie i dodano do nowej galerii link z `/odwazne/`.

### Nowe grafiki aranżacyjne
Przygotowane we wbudowanym ImageGen, lokalne WebP; nie stanowią deklaracji dostępności pokazanych produktów:
- `rose-jewels.webp`, 1536×1024: unbranded gold sculptural necklace, cuff and ring on layered deep rose/magenta velvet, dramatic pink/red rim light, tactile luxury editorial photography, no text/logos.
- `amber-macro.webp`, 1774×887: cinematic closeup gold chain and brushed ring on translucent amber glass, copper glow, textured metal, dark left third for copy, no text/logos.
- `tech-lime.webp`, 1536×1024: black game controller, silver/white headphones and smartphone on vivid lime architectural steps, violet edge shadows, realistic commercial studio photo, no text/logos.

### Weryfikacja
- Przejrzano wszystkie 10 pierwszych ekranów na komputerze i telefonie oraz sekcje ofert na komputerze.
- Każdy mobilny dokument ma clientWidth = scrollWidth = 375 px; wszystkie obrazy załadowane.
- Sprawdzono zmianę kategorii Aurora, panel Panorama, karuzelę Chrom, akordeon Rytm, panel Impuls i odpowiedzi Sygnał.
- Sprawdzono szczegóły oferty Ogrody i Aksamit oraz otwieranie i zamykanie kalkulatora Mozaika i Horyzont.
- Kalkulator: 5000 zł / 30 dni = 250 zł opłaty i 5250 zł łącznie; kwota 0 pokazuje błąd i usuwa nieprawidłowy odnośnik kontaktowy. Nie wysyłano wiadomości.
- Sprawdzono powiększenie projektu, przełączanie urządzenia i wspólne przejście do sekcji oferty. Poprawiono zbyt szeroki mobilny nagłówek Chrom.
- 11 dokumentów HTML: jeden main i h1, brak powielonych identyfikatorów, kompletne kotwice i lokalne zasoby. Składnia JS oraz `git diff --check` bez błędów.
- Podgląd końcowy: `docs/sezam-ten-more-preview.jpg`.


## Podstrony i cennik — 19.11.2026
Wybrany projekt: `sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site`.
Strona główna zachowuje pełną kompozycję zaakceptowanej wersji sprzed podziału: hero, cztery kafelki, ofertę z zakładkami i kartami metali, kalkulator, O nas, baner sprzedaży, FAQ i kontakt. Te same sekcje mają również osobne adresy:
`/oferta/`, `/cennik-zlota/`, `/kalkulator/`, `/o-nas/`, `/pytania/`, `/kontakt/`.
Menu, stopka i breadcrumbs prowadzą do podstron. Kotwice na stronie głównej przewijają do przywróconych sekcji, a kafelki usług wybierają odpowiednią zakładkę oferty. Przycisk cennika i odnośnik w FAQ otwierają nowy cennik. Wybrana usługa na podstronie oferty jest zapisana w `?usluga=`. Każda strona ma własny tytuł, opis, canonical i jeden H1. Generator aktualizuje sitemap.

Cennik korzysta z publicznego endpointu używanego przez aktualną stronę SEZAM:
`https://skup-zlota-gorzow.angsm111.workers.dev/api/prices`.
Złoto/srebro, biżuteria i złom, monety oraz sztabki. Ceny są końcowymi cenami skupu z feedu — nie dodajemy kolejnej marży. Kalkulator mnoży cenę za gram przez masę lub cenę produktu przez liczbę sztuk. Brak ceny i nieznana próba wymagają indywidualnej wyceny.

Odświeżanie co 5 minut, timeout 12 sekund, maksymalny wiek feedu 15 minut. Przeterminowane lub zastępcze dane nie są prezentowane jako aktualne. CORS endpointu sprawdzony. Wyświetlany czas aktualizacji jest w Europe/Warsaw. Bez JavaScript dostępna informacja i telefon, bez fikcyjnych stałych cen.

Sprawdzenie aktualizacji: 7 stron na mobilnym viewport 390 px (375 px treści), bez poziomego przewijania i uszkodzonych obrazów; menu mobilne, aktywna pozycja, ponowne otwarcie wybranej usługi, FAQ, otwarcie i zamknięcie formularza. Kalkulator pożyczki 5000/30 = 250 zł i 5250 zł łącznie; walidacja zera. Cennik: świeży feed, złoto/srebro, wyszukiwarka i wybór monet, sztabki, mnożenie ilości, błędna waga, edycja podczas ładowania. Kontrole Node: świeży/stary/błędny feed, brak dodatkowej marży, nieznane produkty, syntax check. Formularzy nie wysyłano.

## Dwa warianty strony głównej
- `/` — pełna strona główna sprzed podziału na podstrony; zachowane wszystkie sekcje wersji 9, z działającym odnośnikiem do nowego cennika.
- `/wersja-obecna/` — zachowana skrócona strona główna z wersji 10 (`0f9428ce5652ad21b69c3f41e93319b510fe824d`). Bazą jest zapisany wcześniej wariant; późniejsze wspólne dodatki opisano poniżej. Jego pierwotny stan zachowano w historii oraz kopii GitHub.
- Wspólny przełącznik pozwala wrócić do obu wariantów z każdej podstrony. Podstrony usług i cennika są wspólne. Drugi wariant ma własny canonical i noindex; nie jest dodawany do sitemap.
- Oba warianty odtwarza `python3 scripts/build-pages.py`. Zmiany wcześniejszych zestawów projektów nie były potrzebne.
- Weryfikacja: przełączanie w obie strony, pełna i skrócona treść, układy komputera i telefonu (390 px viewport / 375 px treści), brak poziomego przepełnienia, aktywacja oferty z kafelka i kalkulator 5000 zł / 30 dni = 250 zł, razem 5250 zł. Przejście do kotwicy nie resetuje zakładki oferty. Kontrola ośmiu stron: kompletne lokalne odnośniki i zasoby, jeden main i H1, brak powtórzonych ID. Składnia JS i git diff --check poprawne.

## Kontakt, opinie i przyjmowane przedmioty — 20.11.2026
- Wspólne menu zawiera „Co przyjmujemy” i bezpośredni przycisk WhatsApp. Wszystkie dziewięć stron wybranego projektu ma zielony pływający przycisk z białym znakiem WhatsApp, czerwoną kropką i dymkiem „Napisz wiadomość”. Numer: +48 601 775 146.
- Kontakt i pełna strona główna mają „Wyznacz trasę” do Pocztowej 11 oraz bezpośredni przycisk WhatsApp.
- Obie strony główne i Kontakt zawierają informację „Ponad 300 opinii w Google”, podaną przez właściciela, z odnośnikiem do wizytówki. Nie dodawano niepotwierdzonej oceny.
- Obie strony główne mają szampański baner „5% za 30 dni dla nowych klientów”, wysoko pod nagłówkiem, z przejściem do kalkulatora.
- `/co-przyjmujemy/`: sześć kategorii i pięć ilustracji z https://lombard-gorzow.pl/co-przyjmujemy.html, sprawdzone 20.11.2026. Obrazy `accepted-*.webp` pochodzą z repozytorium właściciela `angsm111-dot/lombard-gorzow.pl`. Przyciski przygotowują pytanie o wycenę w WhatsApp; niczego nie wysyłają.
- W cenniku wybór srebra zmienia wszystkie trzy przyciski rodzaju przedmiotu na srebrne. Złoty wariant zachowuje wcześniejsze kolory.
- Nowe fragmenty treści: `src/partials/`; style: `enhancements.css`, `categories.css`, `metal-theme.css`. Mobilne menu działa do 1120 px, aby pomieścić nowe pozycje.
- Weryfikacja: budowanie, składnia JS, zgodność szablonów i wygenerowanych stron, dziewięć stron bez uszkodzonych lokalnych odnośników/zasobów i powtórzonych ID. Przegląd komputera, telefonu 390 px oraz szerokości 320 i 1024 px: brak poziomego przepełnienia i uszkodzonych obrazów. Sprawdzono otwieranie/zamykanie menu oraz srebro → biżuteria/monety/sztabki → złoto. Nie wysyłano wiadomości.
- Kopia obu wariantów przed tą aktualizacją: `https://github.com/angsm111-dot/lombardgorzow/tree/backup/sezam-dwie-wersje-2026-11-20`.

## Obrączki, blog i świąteczny nagłówek — 20.11.2026
- Dodano `/obraczki/`: elegancki wstęp, informacje o wyborze modelu i przyciski „Zobacz katalog” do `https://obraczkigorzow.pl/beta/`.
- Dodano `/blog/` oraz cztery oryginalne poradniki (około 500 słów każdy): przygotowanie do pierwszej wizyty, czynniki wyceny złotej biżuterii, przygotowanie telefonu/laptopa oraz pytania przy wyborze zastawu lub sprzedaży. Każdy ma własny adres, tytuł, opis, canonical, BlogPosting, powiązane poradniki i naturalną frazę „lombard Gorzów”.
- Co przyjmujemy: widoczna sekcja „Masz pytanie o zastaw?” i WhatsApp nad kafelkami.
- Nagłówek „Lombard SEZAM” z wektorową czapką na literze M. WhatsApp przeniesiony bezpośrednio obok telefonu. Menu na dużym ekranie zajmuje osobny czytelny rząd; na małym otwiera się przyciskiem.
- Delikatny opad śniegu: 28 płatków (18 na małym ekranie), bez przechwytywania kliknięć. Przycisk włącz/wyłącz, zapamiętywany wybór, wyłączenie przy prefers-reduced-motion oraz pauza w nieaktywnej karcie.
- Cennik: dwa równe przyciski metalu, poniżej trzy równe przyciski kategorii, zgodnie z układem `https://sezam.com.pl/skup-sprzedaz-zlota/` obejrzanym 20.11.2026. Zachowano srebrne kolory po wyborze srebra.
- Zdjęcie obu stron głównych: nowy `assets/sezam-jewelry-bullion.webp` (1536×1024, 177698 B). Wbudowana edycja obrazu: zachowaj istniejące obrączki, pierścionek, łańcuszek, marmurowy podest, perspektywę i światło; dodaj niewielką sztabkę i realistycznego Krugerranda ze springbokiem, opartych o przednią krawędź płyty, z naturalnymi cieniami. Oryginalny obraz zachowano i wykorzystano na stronie Obrączki.
- Sprawdzenie: 15 stron z poprawnymi lokalnymi linkami, zasobami, jednym H1/main i unikalnymi ID. Weryfikacja JSON-LD, mapy strony i zgodności generatora. Przegląd nowych układów na komputerze, 390 px oraz szerokości 320 i 1024 px: bez poziomego przewijania i brakujących obrazów. Sprawdzono menu, link do artykułu, pauzowanie/wznawianie śniegu, położenie WhatsApp i srebrne kategorie. Składnia JS i git diff --check bez błędów.
