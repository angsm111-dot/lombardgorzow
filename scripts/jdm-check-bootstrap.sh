#!/bin/sh
set -eu
PATH=/usr/local/bin:/usr/bin:/bin
export PATH
[ "$(id -un)" = vvictgzv ]
[ "$(id -u)" != 0 ]
umask 077
sezam_home="$(getent passwd vvictgzv | cut -d: -f6)"
[ -n "$sezam_home" ]
[ "$HOME" = "$sezam_home" ]
[ "$(readlink -f "$sezam_home")" = "$sezam_home" ]
[ ! -L "$sezam_home" ]
[ "$(find "$sezam_home" -maxdepth 0 -type d -user vvictgzv -print)" = "$sezam_home" ]
sezam_web="$sezam_home/public_html"
[ ! -L "$sezam_web" ]
[ "$(find "$sezam_web" -maxdepth 0 -type d -user vvictgzv -print)" = "$sezam_web" ]
sezam_state="$sezam_home/.sezam-nowa-deploy"
[ ! -L "$sezam_state" ]
mkdir -p "$sezam_state"
[ "$(find "$sezam_state" -maxdepth 0 -type d -user vvictgzv -print)" = "$sezam_state" ]
chmod 700 "$sezam_state"
for sezam_guard in "$sezam_state/preparation-bootstrap.lock" "$sezam_state/preparation.log" "$sezam_state/previous-check.txt" "$sezam_state/previous-inventory-check.txt" "$sezam_state/previous-content-check.txt" "$sezam_web/sezam-bootstrap-check.txt" "$sezam_web/sezam-inventory-check.txt" "$sezam_web/sezam-content-check.txt"; do
  [ ! -L "$sezam_guard" ]
  if [ -e "$sezam_guard" ]; then [ "$(find "$sezam_guard" -maxdepth 0 -type f -user vvictgzv -print)" = "$sezam_guard" ]; fi
done
exec 9>"$sezam_state/preparation-bootstrap.lock"
flock -n 9
if [ -f "$sezam_web/sezam-bootstrap-check.txt" ]; then mv -f -- "$sezam_web/sezam-bootstrap-check.txt" "$sezam_state/previous-check.txt"; fi
if [ -f "$sezam_web/sezam-inventory-check.txt" ]; then mv -f -- "$sezam_web/sezam-inventory-check.txt" "$sezam_state/previous-inventory-check.txt"; fi
if [ -f "$sezam_web/sezam-content-check.txt" ]; then mv -f -- "$sezam_web/sezam-content-check.txt" "$sezam_state/previous-content-check.txt"; fi
sezam_tmp="$(mktemp "$sezam_state/preparation.XXXXXXXX")"
sezam_public_tmp=''
trap 'rm -f -- "$sezam_tmp" "$sezam_public_tmp"' EXIT
sezam_log="$sezam_state/preparation.log"
if curl --proto =https --tlsv1.2 --fail --silent --show-error --connect-timeout 20 --max-time 60 https://raw.githubusercontent.com/angsm111-dot/lombardgorzow/a2563129f2d7a873395bfd9516cf477b21789f4c/scripts/prepare-jdm-static.php -o "$sezam_tmp" 2>"$sezam_log" && echo "a8bec3261cde51c916ad3a622fb8c20ba850625c60da4dc933a1cb6aa865a461  $sezam_tmp" | sha256sum --check --status 2>>"$sezam_log" && php -l "$sezam_tmp" >>"$sezam_log" 2>&1; then
  php "$sezam_tmp" --check >"$sezam_log" 2>&1 || true
else
  echo 'Preparation stopped: pinned checker download, checksum or PHP syntax check failed.' >"$sezam_log"
fi
[ ! -L "$sezam_web" ]
[ "$(find "$sezam_web" -maxdepth 0 -type d -user vvictgzv -print)" = "$sezam_web" ]
[ ! -e "$sezam_web/sezam-bootstrap-check.txt" ]
[ ! -L "$sezam_web/sezam-bootstrap-check.txt" ]
sezam_public_tmp="$(mktemp "$sezam_web/sezam-check.XXXXXXXX")"
sed -n '/^Preparation stopped: /p;/^Checks passed: /p;/^Already prepared: /p' "$sezam_log" | head -c 4096 >"$sezam_public_tmp"
if [ ! -s "$sezam_public_tmp" ]; then echo 'Preparation stopped: no recognized checker result; private log requires review.' >"$sezam_public_tmp"; fi
chmod 644 "$sezam_public_tmp"
mv -- "$sezam_public_tmp" "$sezam_web/sezam-bootstrap-check.txt"
