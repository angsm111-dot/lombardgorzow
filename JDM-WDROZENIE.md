# Podgląd JDM — wdrożony

Od 20 listopada 2026 wszystkie trzy wersje działają na niezależnej stronie HTML JDM nr `23048`, pod domeną `nowa.lombardgorzow.com`:

| Wersja | Adres |
| --- | --- |
| 1 — główna | https://nowa.lombardgorzow.com/ |
| 2 — druga strona główna | https://nowa.lombardgorzow.com/wersja-obecna/ |
| 3 — zachowana wersja pierwotna | https://nowa.lombardgorzow.com/wersja-pierwotna/ |

Istniejący WordPress na `lombardgorzow.com` pozostał bez zmian. Nie wykonano jego kopii ani archiwum i nie zapisywano plików w jego katalogu. Kod podglądu i aktualizacje są na gałęzi [`work/sezam-kontakt-cennik`](https://github.com/angsm111-dot/lombardgorzow/tree/work/sezam-kontakt-cennik); `main` i gałąź kopii źródeł pozostały bez zmian.

## Potwierdzone wdrożenie

Pierwsze zweryfikowane wdrożenie zakończyło się `2026-11-20T12:07:04Z`, z commitu [`6b0fd5b6f39703b15674dccf209ee5d3791ed2ed`](https://github.com/angsm111-dot/lombardgorzow/commit/6b0fd5b6f39703b15674dccf209ee5d3791ed2ed): 210 plików i 22 sprawdzone pliki zamrożonej wersji 3. Kontrola HTTP potwierdziła odpowiedzi 200 dla trzech wersji, oryginalnej strony w ramce i 38 sprawdzonych zasobów; wszystkie 22 chronione pliki miały identyczne SHA-256 jak źródła. W przeglądarce sprawdzono przełączanie wersji, aktualne ceny oraz srebrne przyciski kategorii po wyborze srebra.

Cloudflare kieruje rekord `A nowa` na `88.99.51.237` w trybie DNS-only. Dotychczasowe rekordy domeny głównej pozostały bez zmian. HTTPS jest aktywne dla `nowa.lombardgorzow.com` i `www.nowa.lombardgorzow.com`. Na nowej stronie wyłączono i wyczyszczono wszystkie trzy tryby cache NGINX; Redis pozostaje wyłączony. Dotyczy to wyłącznie strony JDM `23048`.

Aktualny commit i wynik wdrożenia są dostępne w [deployment-status.json](https://nowa.lombardgorzow.com/deployment-status.json). Krótki komunikat działania skryptu znajduje się w [sezam-deployment-check.txt](https://nowa.lombardgorzow.com/sezam-deployment-check.txt). Kolejne commity dokumentacji także mogą zmienić identyfikator raportowany przez cykliczne wdrożenie, bez zmiany plików strony.

## Aktualizacje z GitHuba

Natywny Cron JDM działa co 5 minut na koncie `vvictgzv`, wyłącznie dla `/home/vvictgzv/public_html`. Pobiera przypięty skrypt `scripts/jdm-apply-deploy-bootstrap.sh`, sprawdza SHA-256 i uruchamia go. Skrypt osobno weryfikuje przypięte pliki PHP i ich składnię. Deployer odczytuje aktualny commit gałęzi roboczej przez publiczne API GitHuba, pobiera archiwum przypięte do tego commitu i publikuje wyłącznie dozwolone statyczne pliki `dist/`. Nie korzysta z tokenów, haseł, GitHub Actions ani SFTP.

Przypięte wersje wykonywalne:

| Plik | Commit | SHA-256 |
| --- | --- | --- |
| `scripts/jdm-apply-deploy-bootstrap.sh` | `6b0fd5b6f39703b15674dccf209ee5d3791ed2ed` | `b93f807fb52c72603aeaacaf7a0ac43cc491751cb0927dad39466982d6529028` |
| `scripts/prepare-jdm-static.php` | `420e375b259964d2da941a62fe295ea5f7db8dcb` | `ada2b40b7e3152c3091eef85156fd465f1da4388555818388eb6233ccee0c5a3` |
| `scripts/deploy-jdm.php` | `420e375b259964d2da941a62fe295ea5f7db8dcb` | `68aacc212a591703e8481d2ce27e23ca6b7d4e56a9f70aeb095eb3d5791219d4` |

Zmiana skryptów wykonywalnych wymaga przeglądu oraz aktualizacji przypiętych commitów i sum. Ruchoma nazwa gałęzi służy pobieraniu statycznej treści, nie skryptu uruchamianego przez Cron.

Pole polecenia w panelu JDM ma ograniczenia: stosowane polecenie ma 661 znaków i nie zawiera apostrofów, znaku `<` ani `%`. Długie polecenie nie zostało zachowane, apostrofy powodowały problemy z interpretacją, a fragment od `<` do następnego `>` był usuwany. Pełna logika znajduje się więc w zweryfikowanym pliku skryptu, a pole Cron zawiera tylko krótki kod pobrania, kontroli sumy i uruchomienia. Te ograniczenia dotyczą pola panelu, nie zawartości pobranego skryptu.

Deployer wymaga PHP CLI z `posix`, `curl` i `zip`. Sprawdza konto, właścicieli, typy i ścieżki plików; odrzuca dowiązania oraz WordPress/PHP w katalogu publikacji. Manifest i wszystkie 22 pliki wersji 3 muszą zgadzać się przed zapisem. Nowe katalogi publiczne otrzymują `0755`, prywatne `0700`; istniejące prywatne uprawnienia pozostają bez zmian. Publikacja zastępuje pliki atomowo pojedynczo, a główny `index.html` zapisuje na końcu. Nie usuwa innych plików strony. Blokady zapobiegają nakładaniu uruchomień; identyczny, już wdrożony commit nie wymaga ponownego pobrania archiwum.

## Wykonane przygotowanie nowej strony

Mimo wyboru pustej strony JDM dostarczył początkowy instalator WordPressa. Bezpośrednio przed zatwierdzeniem operacji, 20 listopada 2026, panel `https://panel.jdm.pl/website/23048/wordpress` potwierdził domenę `nowa.lombardgorzow.com`, komunikat „WordPress czeka na konfigurację”, wersję 7.1.5 i konto `vvictgzv` na `web13`. Rozpoznane pliki, brak uploads oraz ograniczenia właścicieli i ścieżek potwierdziły zakres nowego, nieuruchomionego instalatora.

`scripts/prepare-jdm-static.php` przeniósł cały katalog tego nowego instalatora przez zmianę nazwy na `/home/vvictgzv/.jdm-unused-installer-23048` z dostępem `0700`, po czym utworzył pusty `public_html` z `0755`. To przeniesienie, bez kopiowania, archiwizacji czy usuwania plików. Skrypt nie uruchamia WordPressa ani WP-CLI i nie łączy się z bazą danych. Zachowuje rollback na wypadek nieudanego utworzenia nowego katalogu. Prywatny znacznik ukończenia pozwala kolejnym uruchomieniom przejść do aktualizacji statycznej strony bez ponownego przenoszenia instalatora.

Zidentyfikowane wyjątki dostarczone przez JDM pozostają ściśle ograniczone:

- `wp-content/object-cache.php`: zwykły plik, UID `0`, grupa konta `3873`, tryb `0750`, rozmiar `49029` bajtów;
- `wp-content/install.php`: właściciel konta strony, `0750`, `16165` bajtów;
- `wp-content/mu-plugins/jdm.php`: właściciel konta strony, `0750`, `1116` bajtów;
- `wp-content/mu-plugins/jdm-plugins`: katalog `0750` oraz należące do konta zwykłe pliki i katalogi jego poddrzewa, bez dowiązań.

Pozostałe pliki nadal podlegają pełnym kontrolom właściciela i typu. Wymienione elementy przeniesiono wraz z nowym instalatorem bez zmiany ich zawartości. Dawne własne pliki diagnostyczne przenoszone są do prywatnego stanu; skrypty nie przenoszą dowolnych plików z katalogu strony. Przygotowanie jest ograniczone do konta `vvictgzv` i dokładnego domu `/home/vvictgzv`; domyślny tryb to `--check`, a przeniesienie wymaga `--apply`.

## Powtarzalny eksport statyczny

Lokalna alternatywa, wymagająca Pythona 3.9 lub nowszego:

```sh
python3 scripts/export-jdm.py
```

W ignorowanym `output/jdm-nowa/` powstają `site/`, `nowa-lombardgorzow-com.zip` i `verification.json`. Eksport nie zmienia źródeł `dist/` ani istniejącego podglądu Sites. Adresy kanoniczne, sitemap i BlogPosting wskazują nową domenę. HTML poza zamrożoną wersją 3 otrzymuje `noindex,nofollow`; wszystkie 22 chronione pliki pozostają identyczne. `robots.txt` blokuje pobieranie przez respektujące go roboty, ale sam nie gwarantuje wykluczenia adresów z indeksu. Są to ustawienia podglądu testowego.

ZIP ma powtarzalną kolejność, daty i uprawnienia, zawiera wyłącznie statyczną stronę i nie zawiera WordPressa. Na JDM nie potrzeba Pythona ani Node. Do sprawdzania endpointu cen należy używać GET, ponieważ nie obsługuje HEAD.
