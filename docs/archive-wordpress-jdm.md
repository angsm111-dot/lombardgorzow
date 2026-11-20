# Archiwalny WordPress na stara.lombardgorzow.com

Pomocnik `scripts/archive-wordpress-jdm.sh` dotyczy wyłącznie istniejącej witryny JDM **11344**, konta **lombard1**, serwera **web16** (`157.90.133.54`) i katalogu `/home/lombard1/public_html`. Nie przenosi plików WordPressa ani nie eksportuje bazy. Alias `stara.lombardgorzow.com` ma wskazywać ten sam istniejący WordPress; nowa strona działa osobno.

**Stan: wykonano wyłącznie `--check`, który zatrzymał się na błędzie audytu WP-CLI przed zmianami WordPressa. `--apply` nie został wykonany.** Nie uruchamiać `--apply`, dopóki docelowa domena nie pokazuje zweryfikowanej nowej wersji 5. Skrypt przed uruchomieniem WP-CLI blokuje lokalne i nadrzędne pliki `wp-cli.yml`/`wp-cli.local.yml`, ponieważ mogą zawierać własne hooki lub kierować polecenia na inny serwer. Dodatkowo sprawdza nową stronę HTTPS: marker `page-home-calculator`, domenę docelową i brak zależności `/wp-content/`. Błędny wynik zatrzymuje pracę przed zmianami WordPressa.

## Kontrola — domyślne działanie

Na JDM należy uruchomić jako użytkownik `lombard1`, nie jako root ani konto nowej strony:

```bash
bash /PRYWATNA-SCIEZKA/archive-wordpress-jdm.sh --check
```

Brak argumentu oznacza to samo co `--check`. Kontrola wywołuje odczyty WP-CLI i `search-replace --dry-run`; nie zapisuje ustawień, plików strony ani stanu migracji. Pokazuje dostępność/wersję WP-CLI, `home`, `siteurl`, ustawienia `WP_HOME`/`WP_SITEURL`, prefiks i liczbę tabel, liczbę opublikowanych artykułów/stron/mediów oraz planowaną liczbę zmian. Nie drukuje konfiguracji bazy, danych logowania, zawartości rekordów ani surowych błędów WP/SQL.

WP-CLI pomija zwykłe wtyczki, motyw i pakiety. WordPress nadal może wczytać swoje istniejące must-use plugins i drop-ins — jest to zachowanie WP-CLI. Pomocnik nie wyłącza ich przez zmianę plików. Raport należy obejrzeć przed zastosowaniem; referencyjna inwentaryzacja starej witryny obejmowała **41 wpisów oraz 17 stron**.

Stałe `WP_HOME` i `WP_SITEURL`, niestandardowe lokalizacje treści, jawne `WP_CONTENT_URL`/`WP_PLUGIN_URL`/`UPLOADS`, multisite, współdzielone tabele użytkowników, drugi zestaw tabel `options` z tym samym prefiksem albo tabele bez klucza głównego blokują migrację. Skrypt niczego nie poprawia w `wp-config.php`. Jeśli raport wykryje taki przypadek, trzeba najpierw przejrzeć konkretną konfigurację i uzgodnić jej poprawkę.


## Gdy kontrola kończy się ogólnym błędem audytu

`--diagnose` służy wyłącznie do odczytu i rozpoznania etapu błędu:

```bash
bash /PRYWATNA-SCIEZKA/archive-wordpress-jdm.sh --diagnose
```

Raport błędu powstaje w Bashu i nie zależy od możliwości odczytu prywatnych plików przez PHP. Wykonuje trzy ograniczone próby: `wp eval --skip-wordpress`, samo uruchomienie WordPressa oraz ten sam pełny audyt co `--check`. Nie wykonuje zamiany URL-i ani aktualizacji opcji, nie instaluje wtyczki i nie dotyka plików WordPressa. Nadal obowiązują wszystkie ograniczenia konta, hosta, ścieżki i konfiguracji WP-CLI.

Surowe stdout/stderr trafiają do nowego katalogu `run.*` w `/home/lombard1/sezam-wp-archive-state/diagnostics/`, poza `public_html`. Katalogi mają `0700`, a logi `0600`. Logi mogą zawierać wewnętrzne szczegóły błędu; nie kopiować ich do pliku publicznego. Publiczny wynik zawiera wyłącznie zdefiniowane nazwy etapów, kod zakończenia, kategorię błędu, informacje o obecności znacznika, ostrzeżeń/deprecjacji, liczbę bajtów oraz ogólne kategorie komponentów. Już próba bez WordPressa pokazuje zweryfikowany format wersji PHP używanej przez WP-CLI i dostępność mysqli. Udany bootstrap dodatkowo pokazuje logiczną informację o obecności hooka konfiguracji. Nazwy baz, użytkowników DB, hasła, treść konfiguracji, SQL, ścieżki z tracebacków i fragmenty surowych błędów nie są przekazywane do raportu.

Przykłady interpretacji: `eval_without_wordpress=ok` i błąd `wordpress_bootstrap` wskazują na ładowanie WordPressa lub jego drop-ins/MU plugins. Udany bootstrap i błąd `full_readonly_audit` wskazują na konkretny warunek lub zapytanie audytu. `config_hook_missing` nazywa dokładny warunek ochronny helpera. `expected_marker_missing` przy exit0 pozwala odróżnić brak oczekiwanego wyjścia od błędu procesu. Dodatkowy `php_classifier_probe` jednokrotnie odtwarza wcześniejszy błąd klasyfikatora PHP, zachowuje jego stderr prywatnie i publikuje już tylko kategorię rozpoznaną w Bashu (np. `filesystem_open_basedir`, `cli_argv_unavailable`, `php_file_read_unavailable`). Jego błąd nie przerywa kolejnych prób. Kategoria `unclassified_failure` oznacza potrzebę prywatnego przeglądu, nie zgodę na pokazanie całego logu.

## Zastosowanie po przełączeniu domeny

```bash
bash /PRYWATNA-SCIEZKA/archive-wordpress-jdm.sh --apply
```

Kolejność:

1. Ponownie wykonuje pełny odczyt i dry-run. Sprawdza nową produkcję oraz alias archiwum przez HTTPS. Sam status 200/301 nie wystarcza: bez podążania za przekierowaniem pobiera przez alias znany publiczny rekord REST starego WordPressa (ID 14219 i jego dokładny slug). Brak dostępu do REST lub niezgodny wynik zatrzymuje migrację do wyjaśnienia routingu.
2. Zakłada blokadę tylko dla tego konta. Zapisuje mały plik `/home/lombard1/sezam-wp-archive-state/original-settings.json` z pierwotnymi URL-ami, `blog_public`, licznikami i identyfikatorami kontroli. To metadane cofnięcia ustawień, **nie kopia WordPressa i nie eksport bazy**.
3. Instaluje własny plik `wp-content/mu-plugins/sezam-old-site.php`, nie nadpisując istniejącego pliku pod tą nazwą. Wtyczka działa tylko dla nagłówka hosta `stara.lombardgorzow.com`: wysyła `X-Robots-Tag: noindex, follow`, dodaje regułę `wp_robots`, wyłącza mapę WordPressa i pokazuje widoczny pasek z linkiem do nowej strony. Pozwala robotom odczytać `noindex`.
4. Uruchamia WP-CLI `search-replace` z `--all-tables-with-prefix --skip-columns=guid --precise --recurse-objects`. W jednym przebiegu dopasowuje cztery warianty `http(s)://[www.]lombardgorzow.com`, także ze slashami zapisanymi jako `\/` w JSON. Granica nazwy hosta chroni podobne, ale inne domeny. Zmienia je na `https://stara.lombardgorzow.com`; serializacja PHP jest obsługiwana przez WP-CLI.
5. Ustawia `home` i `siteurl` na adres archiwum oraz `blog_public=0`. Unieważnia wyłącznie wpisy cache postów i opcji tego WordPressa; nie wykonuje globalnego `wp cache flush`.
6. Sprawdza URL-e, liczby treści, tożsamość bazy i zestaw tabel oraz brak dawnych URL-i poza celowo pomijanym `guid`.

Istniejący stan migracji lub plik wtyczki zatrzymują ponowne `--apply`. Przerwanej migracji nie należy uruchamiać ponownie w ciemno: stan pozostaje do przeglądu, a skrypt nie usuwa go automatycznie. Operacja nie jest jedną transakcją SQL. Jeżeli błąd wystąpi po rozpoczęciu zamiany, część zmian mogła już zostać zapisana.

Po zastosowaniu sprawdź stronę, przykładowy artykuł, zdjęcia, logowanie i nagłówek `X-Robots-Tag` na archiwum. Jeżeli istnieje cache HTML/CDN/hostingu, wyczyść **tylko cache starej witryny** i powtórz sprawdzenie. Nie wykonuj globalnego czyszczenia Redis ani cache innych witryn. Skrypt nie zmienia routingu JDM, DNS, certyfikatów ani plików nowej strony.

## Cofnięcie konfiguracji — polecenia do świadomego uruchomienia

Poniższe polecenia są instrukcją cofnięcia; pomocnik **nie wykonuje ich automatycznie**. Najpierw potwierdź, że jesteś na `web16` jako `lombard1` i że `--check` wskazuje tę samą witrynę. Przy przerwanym wdrożeniu najpierw obejrzyj pole `status` w pliku stanu. Nie przywracaj routingu domeny do starego WordPressa przed sprawdzeniem przywróconych ustawień.

```bash
# Sesja jako lombard1 na web16; ścieżki celowo ustalone na sztywno.
cd /home/lombard1/public_html
export WP_CLI_CONFIG_PATH=/dev/null
ARCHIVE_STATE=/home/lombard1/sezam-wp-archive-state/original-settings.json
ARCHIVE_OLD_HOME=$(php -r '$s=json_decode(file_get_contents($argv[1]),true); echo $s["home"];' "$ARCHIVE_STATE")
ARCHIVE_OLD_SITEURL=$(php -r '$s=json_decode(file_get_contents($argv[1]),true); echo $s["siteurl"];' "$ARCHIVE_STATE")
ARCHIVE_OLD_PUBLIC=$(php -r '$s=json_decode(file_get_contents($argv[1]),true); echo $s["blog_public"];' "$ARCHIVE_STATE")
ARCHIVE_WP=(wp --path=/home/lombard1/public_html --skip-plugins --skip-themes --skip-packages --no-color)

# Najpierw obejrzyj wyłącznie licznik planowanych zmian.
"${ARCHIVE_WP[@]}" search-replace 'https://stara.lombardgorzow.com' "$ARCHIVE_OLD_HOME" \
  --all-tables-with-prefix --skip-columns=guid --precise --recurse-objects --dry-run --format=count

# Dopiero po weryfikacji wyniku wykonaj cofnięcie adresu w danych.
"${ARCHIVE_WP[@]}" search-replace 'https://stara.lombardgorzow.com' "$ARCHIVE_OLD_HOME" \
  --all-tables-with-prefix --skip-columns=guid --precise --recurse-objects --format=count
"${ARCHIVE_WP[@]}" option update home "$ARCHIVE_OLD_HOME"
"${ARCHIVE_WP[@]}" option update siteurl "$ARCHIVE_OLD_SITEURL"
"${ARCHIVE_WP[@]}" option update blog_public "$ARCHIVE_OLD_PUBLIC"

# Wyłącz wyłącznie wtyczkę zainstalowaną przez ten pomocnik; zachowaj jej plik.
ARCHIVE_DISABLED="/home/lombard1/sezam-wp-archive-state/sezam-old-site.disabled.$(date -u +%Y%m%dT%H%M%SZ).php"
mv -- /home/lombard1/public_html/wp-content/mu-plugins/sezam-old-site.php "$ARCHIVE_DISABLED"

# Cache tylko tego WordPressa, bez globalnego flush.
"${ARCHIVE_WP[@]}" eval 'global $wpdb; foreach ($wpdb->get_col("SELECT ID FROM `".$wpdb->posts."`") as $id) { clean_post_cache((int)$id); } foreach ($wpdb->get_col("SELECT option_name FROM `".$wpdb->options."`") as $key) { wp_cache_delete($key,"options"); } wp_cache_delete("alloptions","options"); wp_cache_delete("notoptions","options");'

# Kontrola przywróconych wartości (bez odczytu konfiguracji DB).
"${ARCHIVE_WP[@]}" option get home
"${ARCHIVE_WP[@]}" option get siteurl
"${ARCHIVE_WP[@]}" option get blog_public
```

Cofnięcie odtwarza dokładne pierwotne wartości trzech ustawień. W treści normalizuje dawne warianty HTTP/HTTPS/www do pierwotnego `home`; nie odtwarza bajt w bajt wcześniejszego wymieszania tych wariantów ani stylu escapowania JSON. Jeżeli potrzebne jest identyczne odtworzenie każdego rekordu, użyj istniejącej kopii JDM z chwili sprzed migracji — pomocnik nie tworzy dodatkowej kopii i nie obiecuje bezstratnego odwrócenia zamiany wiele-do-jednego. Zachowaj metadane migracji do dalszego przeglądu. Routing JDM/DNS do starej witryny przywraca się osobno, po kontroli jej działania.

Oficjalna dokumentacja: [WP-CLI search-replace](https://developer.wordpress.org/cli/commands/search-replace/), [config has](https://developer.wordpress.org/cli/commands/config/has/), [option update](https://developer.wordpress.org/cli/commands/option/update/).
