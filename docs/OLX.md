# Katalog sprzedaży — lombardgorzow.com

## Źródło i zakres

Strona odbiera wyłącznie **publiczny katalog własnych ofert SEZAM** z istniejącego backendu sezam.com.pl. Nie łączy się z OLX i nie potrzebuje aplikacji, callbacku, Client Secret, tokenów ani sesji OAuth. Istniejące połączenie SEZAM z OLX i odbiorca lombard-gorzow.pl pozostają niezależne.

Architekturę sprawdzono na aktualnych źródłach `angsm111-dot/sezam.com.pl` (`679e897768aed32f11da3172d50b3be14ceb8da1`) i `angsm111-dot/lombard-gorzow.pl` (`42ce170ed2caa8d054204542dad1b9e4bc3db481`). Publiczny katalog źródła pokazywał 20.11.2026 36 aktywnych ofert, z datą danych 2026-11-20. Ta kontrola strony źródłowej nie jest potwierdzeniem wdrożenia nowego odbiorcy.

## Przepływ i harmonogram

OLX → bieżący prywatny katalog na hostingu SEZAM → osobny runner SSH → odbiornik lombardgorzow.com. Nowy runner ma własny klucz, blokadę, status i pozycję crona **`17,47 * * * *`**. Błąd nowego odbiorcy nie zatrzymuje istniejącego przekazywania do lombard-gorzow.pl. Synchronizacja źródła z OLX nadal ma własny harmonogram i ustawienia.

Nowy odbiornik: konto `vvictgzv`, `web13.jdm.pl:2233`, publiczne pliki `/home/vvictgzv/public_html`, prywatne dane `/home/vvictgzv/private/lombardgorzow-catalog`. Klucz prywatny powstaje i pozostaje wyłącznie na hostingu źródłowym. Do docelowego `authorized_keys` trafia tylko dedykowany klucz publiczny z `restrict` i wymuszonym poleceniem PHP. CLI dodatkowo wymaga dokładnie `SSH_ORIGINAL_COMMAND=receive-public-catalog-v1`. Istniejące wpisy `authorized_keys` są zachowywane.

SSH wymaga przypiętego i potwierdzonego klucza hosta. Nie wyłączać `StrictHostKeyChecking`. Publiczny klucz odczytany przez właściciela z hostingu musi zgadzać się z kluczem rzeczywistego `web13.jdm.pl:2233`, zanim zostanie użyty do transferu.

## Format i publikacja

Protokół `sezam-public-offers-v1` przekazuje kompletny manifest z datą źródła, walutą PLN, liczbą produktów i dozwolonymi publicznymi polami: tytuł, opis, cena, kategoria, status, stały slug, identyfikator/URL ogłoszenia, daty i pełna galeria. Nie przekazuje konfiguracji, tokenów, właściciela konta ani surowych prywatnych pól API. Nowy nadawca wymaga bieżącego katalogu runtime; nie importuje kopii ofert z Gita jako danych aktualnych.

Zdjęcia są kopiowane lokalnie, maksymalnie 30 na produkt. Każdy obraz przechodzi kontrolę SHA-256, typu, rozmiaru i wymiarów. Odbiornik pyta wyłącznie o brakujące obrazy. Nazwy `/assets/sales-feed-<sha256>.<jpg|png|webp>` są zależne od treści. Żaden nagłówek OAuth nie jest potrzebny.

Wspólna blokada i atomowa podmiana `data/catalog.json` chronią ostatni poprawny odczyt. Niepełna przesyłka, starsze dane, duplikaty, nieprawidłowy obraz lub rozłączenie nie zastępują opublikowanego katalogu. Poprzedni poprawny snapshot pozostaje w `data/catalog.previous.json`. Zmiana tytułu nie zmienia sluga przypisanego do identyfikatora ogłoszenia. Przedmiot, którego nie ma w kompletnym nowym katalogu, otrzymuje status niedostępny; zachowuje adres, opis i zdjęcia.

`source_checked_on` i `checked_on` oznaczają datę informacji w SEZAM. Prywatne `synced_at`, `last_attempt`, `last_success` opisują import. Ponowne dostarczenie tych samych danych nie jest nowym odczytem OLX i nie przesuwa daty danych pokazywanej klientom.

## Publiczne adresy i wygląd

- `/na-sprzedaz/` — katalog, dostępny także bez JavaScript.
- `/na-sprzedaz/<kategoria>/` — kategorie z widocznymi licznikami, również na telefonie.
- `/na-sprzedaz/<slug>/` — stałe podstrony przedmiotów, pełne galerie, cena, opis, WhatsApp i oryginalne ogłoszenie OLX.
- `/integracje/katalog/oferty/` — publiczna projekcja JSON, bez konfiguracji i danych dostępowych; noindex.
- `/integracje/katalog/mapa/` — aktualna mapa kategorii i produktów.

Kategorie pochodzą z katalogu źródłowego. Dodatkowy filtr „Pierścionki” obejmuje również sygnety rozpoznane w biżuterii; nie zmienia źródłowej kategorii. Kategorie bez ofert są ukrywane, ale wybrana pusta kategoria zachowuje swój adres. Dostępne/zarezerwowane przedmioty liczone są raz w „Wszystkie przedmioty”. JS pokazuje 24 pozycje i umożliwia rozwinięcie następnych; bez JS dostępna jest pełna lista. Galeria pokazuje wszystkie obrazy. Niedostępne produkty mają informację dla użytkownika i `schema.org/OutOfStock`.

Katalog zachowuje perłowe tła, grafit i szampańskie akcenty wersji 5. Telefon, WhatsApp i adres firmy pozostają zgodne z projektem: 601 775 146, Pocztowa 11, Gorzów Wielkopolski.

## Granice zwykłego wdrożenia strony

`scripts/build-pages.py` buduje statyczny placeholder `/na-sprzedaz/index.html` oraz pełny szablon `/assets/sales-template.html`. Placeholder ma marker `SEZAM_SALES_PLACEHOLDER`; szablon ma marker `SEZAM_SALES_TEMPLATE_V1`. Szablon jest zwykłym HTML, służy aktualizacji wspólnego menu, logo i stopki i nie jest indeksowany. Renderer czyta go jako tekst, nigdy jako kod, i zastępuje treść oraz metadane danej strony.

Po instalacji odbiornika zwykły deploy pomija placeholder i chroni przestrzeń runtime: `/na-sprzedaz/`, `/integracje/katalog/` oraz `/assets/sales-feed-*`. Nie usuwa prywatnych danych, konfiguracji, klucza ani ostatniego katalogu. Instalator usuwa wyłącznie rozpoznany placeholder; nie zastępuje obcej strony.

Publiczne PHP to identyczny, ściśle przypięty bootstrap wymagający prywatnego `current/router.php`. SHA-256: `0386468c7f866cdf66936701f0e8ddd45a962d450f8efc0e3411e61099945233`. Wdrożenie dopuszcza go jedynie pod określonymi ścieżkami i gdy prywatny `catalog-active.json` potwierdza `schema=1`, `site_id=23048` i zgodny hash. Archiwum zwykłej strony nadal nie może zawierać PHP. Instalacja i deploy współdzielą `deployment.lock`.

Prywatne wydania kodu są wersjonowane, a `current` wskazuje wybrane wydanie. Aktualizacja kodu zachowuje konfigurację i runtime. Tryb odbioru można wstrzymać bez usuwania danych. Żadne testowe oferty nie należą do eksportu strony.

## Kontrola przed uruchomieniem

Kontrola offline: `php integrations/catalog-receiver/tests/protocol.php`. Obejmuje 47 przypadków bez sieci i prawdziwych ofert: kompletny protokół i galerie, zachowanie ostatniego katalogu po błędzie, stabilne slugi, niedostępne produkty, renderowanie/escape, ograniczony klucz, idempotencję i rollback instalatora. W środowisku przygotowania wykonano ją pod PHP-WASM 8.5.12; test na rzeczywistym PHP WWW hostingu pozostaje osobnym krokiem.

1. Sprawdzić lint PHP/JS, testy odbiornika/nadawcy oraz ochronę runtime w deployerze.
2. Opublikować zwykłą stronę wraz ze szablonem i arkuszami. Przygotować prywatny kod z konkretnego przejrzanego commitu.
3. Przygotować nowy klucz na źródle; przekazać wyłącznie publiczną część do ograniczonego odbiornika. Potwierdzić klucz hosta.
4. Zainstalować odbiornik i uruchomić kontrolowaną pierwszą przesyłkę. Włączyć nowy harmonogram dopiero po poprawnym pokwitowaniu.
5. Otworzyć rzeczywiste publiczne PHP WWW. Prywatny `data/web-check.json` potwierdza SAPI, dostęp do katalogu prywatnego i stan `open_basedir`; sukces CLI nie zastępuje tej próby.
6. Porównać aktywną liczbę i kategorie ze świeżym źródłem; sprawdzić wszystkie zdjęcia, filtry, stały URL, produkt niedostępny, desktop i telefon. Potwierdzić nowy `last_success` i zachowanie danych po błędnej/niepełnej przesyłce w testach kontrolnych.
7. Sprawdzić zachowany wpis crona na serwerze i następny udany cykl. Potem zgłosić mapę katalogu wraz z główną mapą w Search Console.

Instalacja z przejrzanego prywatnego stagingu: `php /PRIVATE-STAGING/install.php --release=<pełny-40-znakowy-commit> --sender-key=/PRIVATE-STAGING/sender.pub --enable`. Plik `sender.pub` zawiera tylko publiczną część dedykowanego klucza źródła. Przy kolejnej aktualizacji kodu pominąć `--enable`, aby zachować stan właściciela. Kontrola: `php /home/vvictgzv/private/lombardgorzow-catalog/current/cli.php --check`; pauza i wznowienie: `--disable` / `--enable`. Nie umieszczać stagingu w `public_html`.

Cloudflare nie bierze udziału w dostawie SSH. Nie zmieniać DNS, SSL, poczty ani ochrony domen na potrzeby integracji. Dynamiczne strony katalogu i JSON wysyłają `no-store`; nie obejmować ich regułą cache-everything. Obrazy o nazwach zależnych od treści mogą być cache’owane.

## Stan wdrożenia

Kod przygotowany do weryfikacji i instalacji. **Ten wpis nie potwierdza jeszcze rzeczywistego pierwszego transferu, PHP WWW ani następnego cyklu crona**. Wynik, termin ostatniej udanej przesyłki i docelowe publiczne URL należy dopisać po kontroli na hostingu, bez sekretów.
