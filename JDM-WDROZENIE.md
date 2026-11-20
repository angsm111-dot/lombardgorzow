# Podgląd na nowa.lombardgorzow.com

Zakres wdrożenia: wyłącznie nowa, niezależna strona HTML pod adresem `https://nowa.lombardgorzow.com`. Istniejący WordPress na `lombardgorzow.com` pozostaje bez zmian. Nie tworzymy jego kopii ani archiwum i nie przesyłamy żadnych plików do jego katalogu.

Kod rozwijanej strony jest na gałęzi `work/sezam-kontakt-cennik`, nie na `main`. Wszystkie trzy wersje są dostępne przez przełącznik: `/`, `/wersja-obecna/` oraz `/wersja-pierwotna/`. Wersja 3 ma 22 chronione pliki; eksport zachowuje je bajt w bajt.

## Warunek serwera przed wdrożeniem

Weryfikacja panelu JDM z 20 listopada 2026 wykazała, że nowa strona nr `23048` zawiera nieuruchomiony instalator WordPress 7.1.5, mimo wyboru pustej strony podczas tworzenia. Nie spełnia więc jeszcze warunku niezależnego, pustego katalogu HTML. Wdrożenia oraz zadania Cron nie wolno uruchamiać, dopóki katalog nowej subdomeny nie zostanie bezpiecznie przygotowany i ponownie sprawdzony. Zabezpieczenia skryptu mają pozostać włączone.

Przygotowanie może dotyczyć wyłącznie nowej strony `nowa.lombardgorzow.com`; nie wolno zmieniać działającego WordPressa pod `lombardgorzow.com` ani wykonywać jego kopii lub archiwum. Rekord DNS nowej subdomeny i HTTPS również wymagają oddzielnego potwierdzenia przed publikacją.

## Przygotowanie paczki

Wymagany jest Python 3.9 lub nowszy. Z katalogu repozytorium uruchom:

```sh
python3 scripts/export-jdm.py
```

Skrypt buduje stronę w osobnym katalogu tymczasowym. Nie zmienia źródeł, plików `dist/` ani adresów istniejącego podglądu Sites. W eksporcie podmienia adresy kanoniczne, mapę witryny i dane BlogPosting na nową subdomenę. Do wszystkich plików HTML poza zamrożoną wersją 3 dodaje `noindex,nofollow`; wszystkie pliki wersji 3 pozostają niezmienione. Plik `robots.txt` blokuje pobieranie stron przez respektujące go roboty, ale sam nie gwarantuje wykluczenia adresów z indeksu wyszukiwarki. Jest to ustawienie dla strony testowej, nie docelowej strony produkcyjnej.

Wyniki w ignorowanym katalogu `output/jdm-nowa/`:

- `site/` — gotowe pliki statyczne;
- `nowa-lombardgorzow-com.zip` — paczka do przesłania na JDM;
- `verification.json` — sumy SHA-256 i wynik kontroli plików oraz linków.

Archiwum ma powtarzalną kolejność plików, daty i uprawnienia. Nie zawiera kodu WordPressa ani jego danych. Na serwerze nie potrzeba Pythona, Node ani bazy danych.

## Wgranie na JDM

1. W panelu wybierz niezależną stronę HTML `nowa.lombardgorzow.com` i sprawdź jej dokładny katalog dokumentów.
2. Prześlij ZIP wyłącznie do tego katalogu i rozpakuj jego zawartość. `index.html`, `assets/`, `wersja-obecna/` i `wersja-pierwotna/` muszą znajdować się bezpośrednio w katalogu dokumentów subdomeny.
3. Nie zastępuj konfiguracji ani plików strony `lombardgorzow.com`. Nie uruchamiaj synchronizacji usuwającej pliki w katalogu nadrzędnym.
4. Włącz certyfikat HTTPS dla nowej subdomeny i sprawdź wszystkie trzy wersje, cennik, menu oraz obrazy na telefonie.

Nie dodano GitHub Actions ani dostępu SFTP. Do kontroli źródła cen używaj żądania GET, ponieważ endpoint cen nie obsługuje HEAD.

## Aktualizacje przez natywny Crontab JDM

Przygotowany `scripts/deploy-jdm.php` służy wyłącznie niezależnej stronie HTML JDM nr `23048`, na koncie systemowym `vvictgzv`. Dopuszczalny cel to `public_html` w katalogu domowym tego konta, odczytanym z systemowego rejestru użytkowników. Inne konto, właściciel, dowiązanie symboliczne, ślady WordPressa albo skrypty PHP w katalogu docelowym przerywają działanie przed wdrożeniem.

Skrypt wymaga PHP CLI z modułami `posix`, `curl` i `zip`. Przed pierwszym uruchomieniem należy sprawdzić go na JDM poleceniem `php -l`, używając właściwej ścieżki do PHP udostępnionej przez hosting. Skrypt nie przyjmuje adresu serwera ani katalogu docelowego z argumentów.

Procedura dla Crontaba:

1. Pobierz sam `scripts/deploy-jdm.php` z zatwierdzonego, konkretnego commitu GitHub do prywatnego katalogu `~/.sezam-nowa-deploy/`, poza `public_html`.
2. Sprawdź pobrany plik względem ustalonej wcześniej sumy SHA-256, uruchom `php -l`, a następnie uruchom go jako `vvictgzv`. Nie wykonuj pliku po nieudanej kontroli sumy. Wpis Cron nie powinien pobierać wykonywalnego skryptu z ruchomej nazwy gałęzi.
3. Skrypt przez publiczne API odczyta aktualny commit gałęzi `work/sezam-kontakt-cennik`, a następnie pobierze ZIP przypięty do tego commitu. Nie używa tokenów, haseł ani danych WordPressa. Do katalogu strony trafią jedynie dozwolone pliki statyczne z `dist/`.
4. Przed zapisem skrypt sprawdza zamrożony manifest i wszystkie 22 oryginalne pliki. Dane do pobrania są ograniczone rozmiarem; ścieżki ZIP, właściciele i typy plików są sprawdzane. Metadane domeny, `noindex` w HTML poza wersją 3 i ograniczenie pobierania przez roboty są stosowane tak samo jak w eksporcie ZIP.
5. Każdy plik zastępowany jest atomowo, a główny `index.html` trafia na serwer na końcu. Skrypt nie usuwa plików strony ani katalogów nadrzędnych. Blokada `flock` nie dopuszcza nakładających się wdrożeń. Gdy commit jest już opublikowany, nie pobiera ponownie archiwum.

Prywatny stan i tymczasowe pobranie źródeł są w `~/.sezam-nowa-deploy/`; tymczasowe archiwum GitHub jest usuwane po wykonaniu. Nie jest to kopia ani archiwum WordPressa. Publiczny `deployment-status.json` zawiera tylko adres podglądu, identyfikator tej nowej strony, commit, czas i liczbę plików. Skrypt jest przypięty do zatwierdzonej wersji; jego późniejsza zmiana wymaga ponownego przeglądu i aktualizacji przypiętego commitu oraz sumy w zadaniu Cron.

Wpis Crontab należy tworzyć dopiero po potwierdzeniu dokument root i po przeglądzie skryptu. Zewnętrzne DNS domeny obsługuje Cloudflare; nowy rekord `nowa` należy skonfigurować oddzielnie, bez zmiany rekordów działającej strony głównej.
