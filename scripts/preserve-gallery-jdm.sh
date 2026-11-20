#!/usr/bin/env bash
# Copy only the nine publicly displayed original gallery JPEGs. No WordPress
# configuration, database, other uploads or website content is changed.
set -Eeuo pipefail
umask 077
export LC_ALL=C
readonly ACCOUNT=lombard1
readonly DOCROOT=/home/lombard1/public_html
readonly SOURCE="$DOCROOT/wp-content/uploads/2014/08"
readonly PRIVATE=/home/lombard1/sezam-gallery-preservation
readonly TOKEN=0b34af3ad29902c1e58c442a1617ab59
readonly NAME="galeria-lombardgorzow-2026-11-21-$TOKEN"
readonly ARCHIVE="$PRIVATE/$NAME.tar.gz"
readonly DELIVERY="$DOCROOT/sezam-gallery-$TOKEN.tar.gz"
readonly REPORT="$DOCROOT/sezam-gallery-$TOKEN.json"
stage=account
can_report=false
stop() {
  printf 'Gallery preservation stopped: %s\n' "$stage" >&2
  if [[ "$can_report" == true && ! -e "$REPORT" && ! -L "$REPORT" ]]; then
    failure_tmp="$(mktemp "$DOCROOT/.sezam-gallery-report.XXXXXXXX")"
    printf '{"result":"stopped","stage":"%s","source_unchanged":true}\n' "$stage" > "$failure_tmp"
    chmod 644 "$failure_tmp"
    mv -nT -- "$failure_tmp" "$REPORT"
  fi
  exit 1
}
owned_dir() { [[ -d "$1" && ! -L "$1" && "$(readlink -f "$1")" == "$1" && "$(stat -c '%U' "$1")" == "$ACCOUNT" ]]; }
[[ $# == 0 && "$(id -un)" == "$ACCOUNT" && "$HOME" == /home/lombard1 ]] || stop
owned_dir "$DOCROOT" || stop
for executable in readlink stat sha256sum od tar mktemp cp mv cmp tr cut mkdir chmod; do command -v "$executable" >/dev/null 2>&1 || stop; done
for path in "$ARCHIVE" "$DELIVERY" "$REPORT"; do [[ ! -L "$path" ]] || stop; done
can_report=true
# Repeated panel cron never overwrites a previous result or recreates a removed
# delivery. A new operation would require a newly reviewed token.
[[ ! -e "$REPORT" ]] || exit 0
stage=source
owned_dir "$SOURCE" || stop
files=()
for number in 2 7 6 1 3 4 9 8 5; do
  filename="lmbard-gorzow-$number.jpg"
  stage="source_$filename"
  path="$SOURCE/$filename"
  [[ -f "$path" && ! -L "$path" && "$(readlink -f "$path")" == "$path" && "$(stat -c '%U' "$path")" == "$ACCOUNT" ]] || stop
  size="$(stat -c '%s' "$path")"
  [[ "$size" -ge 4 && "$size" -le 10485760 ]] || stop
  [[ "$(od -An -tx1 -N3 "$path" | tr -d ' \n')" == ffd8ff ]] || stop
  files+=("$filename")
done
stage=private_directory
if [[ ! -e "$PRIVATE" ]]; then mkdir -m 700 "$PRIVATE"; fi
owned_dir "$PRIVATE" && [[ "$(stat -c '%a' "$PRIVATE")" == 700 ]] || stop
[[ ! -e "$ARCHIVE" && ! -e "$DELIVERY" ]] || stop
work="$(mktemp -d "$PRIVATE/gallery.XXXXXXXX")"
owned_dir "$work" && [[ "$(stat -c '%a' "$work")" == 700 ]] || stop
mkdir -m 700 "$work/photos"
report_tmp=''
delivery_tmp=''
cleanup() {
  rc=$?
  trap - EXIT
  [[ -z "$delivery_tmp" ]] || rm -f -- "$delivery_tmp"
  [[ -z "$report_tmp" ]] || rm -f -- "$report_tmp"
  if [[ "$rc" != 0 ]]; then printf 'Gallery preservation stopped: %s; source unchanged.\n' "$stage" >&2; fi
  exit "$rc"
}
trap cleanup EXIT
stage=copy
(cd "$SOURCE" && sha256sum -- "${files[@]}") > "$work/source-before.sha256"
for filename in "${files[@]}"; do
  cp -- "$SOURCE/$filename" "$work/photos/$filename"
  chmod 600 "$work/photos/$filename"
done
(cd "$work/photos" && sha256sum --check --status "$work/source-before.sha256") || stop
(cd "$SOURCE" && sha256sum -- "${files[@]}") > "$work/source-after.sha256"
cmp --silent "$work/source-before.sha256" "$work/source-after.sha256" || stop
(cd "$work" && sha256sum -- photos/*.jpg) > "$work/SHA256SUMS"
cat > "$work/README.txt" <<'TEXT'
Galeria starej strony lombardgorzow.com — zachowane oryginalne pliki.
Źródło: https://lombardgorzow.com/galeria/ (WordPress page ID 10049).
Skopiowano 9 plików JPG, bez zmiany bajtów źródła. Nie jest to kopia WordPressa.
Kolejność w galerii: 2, 7, 6, 1, 3, 4, 9, 8, 5.
Zdjęcia są przechowane do późniejszego wykorzystania; nie dodano ich do menu.
W pliku SHA256SUMS znajdują się sumy kontrolne kopii.
TEXT
stage=archive
tar -C "$work" -czf "$ARCHIVE" -- photos SHA256SUMS README.txt
chmod 600 "$ARCHIVE"
tar -tzf "$ARCHIVE" >/dev/null
hash="$(sha256sum "$ARCHIVE" | cut -d' ' -f1)"
bytes="$(stat -c '%s' "$ARCHIVE")"
stage=delivery
delivery_tmp="$(mktemp "$DOCROOT/.sezam-gallery-download.XXXXXXXX")"
cp -- "$ARCHIVE" "$delivery_tmp"
cmp --silent "$ARCHIVE" "$delivery_tmp" || stop
chmod 644 "$delivery_tmp"
mv -nT -- "$delivery_tmp" "$DELIVERY"
delivery_tmp=''
report_tmp="$(mktemp "$DOCROOT/.sezam-gallery-report.XXXXXXXX")"
printf '{"result":"preserved","photos":9,"source_unchanged":true,"sha256":"%s","bytes":%s,"download":"/sezam-gallery-%s.tar.gz"}\n' "$hash" "$bytes" "$TOKEN" > "$report_tmp"
chmod 644 "$report_tmp"
mv -nT -- "$report_tmp" "$REPORT"
report_tmp=''
printf 'Gallery preservation complete: 9 original JPEGs; source unchanged.\n'
