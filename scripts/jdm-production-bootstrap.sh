#!/bin/sh
# Reviewed immutable deployment payload; outer bootstrap must also be SHA-pinned.
# Existing site 23048 only. Default production; --profile=preview is explicit.
# This script never prepares or moves WordPress.
set -eu
PATH=/usr/local/bin:/usr/bin:/bin
export PATH
sezam_profile=production
if [ "$#" -gt 1 ]; then echo "Only --profile=production or --profile=preview is accepted." >&2; exit 2; fi
if [ "$#" -eq 1 ]; then
  case "$1" in
    --profile=production) sezam_profile=production;;
    --profile=preview) sezam_profile=preview;;
    *) echo "Only --profile=production or --profile=preview is accepted." >&2; exit 2;;
  esac
fi
sezam_commit=d511eacaaa42946dd15cbb667aa0712f37bb61db
sezam_sha256=bca3668b0492e17c8f67454507b079b5e626bce3a3bc327ac35fd1ad2f5f7b56
if [ "${#sezam_commit}" != 40 ] || [ "${#sezam_sha256}" != 64 ]; then
  echo "Production bootstrap is unpinned; nothing executed." >&2
  exit 2
fi
case "$sezam_commit$sezam_sha256" in *[!0-9a-f]*) echo "Invalid deployment pin." >&2; exit 2;; esac

[ "$(id -un)" = vvictgzv ]
[ "$(id -u)" != 0 ]
[ "$HOME" = /home/vvictgzv ]
[ "$(getent passwd vvictgzv | cut -d: -f6)" = "$HOME" ]
[ "$(readlink -f "$HOME")" = "$HOME" ]
umask 077
sezam_state="$HOME/.sezam-nowa-deploy"
sezam_web="$HOME/public_html"

sezam_directory() {
  [ ! -L "$1" ]
  [ "$(find "$1" -maxdepth 0 -type d -user vvictgzv -print)" = "$1" ]
}
sezam_file() {
  [ ! -L "$1" ]
  [ "$(find "$1" -maxdepth 0 -type f -user vvictgzv -print)" = "$1" ]
}
sezam_directory "$HOME"
sezam_directory "$sezam_state"
sezam_directory "$sezam_web"
sezam_file "$sezam_state/static-preparation-23048.txt"
[ "$(cat "$sezam_state/static-preparation-23048.txt")" = 'Prepared SEZAM static site 23048' ]
sezam_file "$sezam_state/deployed.json"
sezam_file "$sezam_web/deployment-status.json"
sezam_file "$sezam_web/index.html"
# Share the old wrapper lock so a transition cannot run both wrappers at once.
for sezam_guard in "$sezam_state/preparation-bootstrap.lock" "$sezam_state/deployment.log" "$sezam_web/sezam-deployment-check.txt"; do
  [ ! -L "$sezam_guard" ]
  if [ -e "$sezam_guard" ]; then sezam_file "$sezam_guard"; fi
done
exec 9>"$sezam_state/preparation-bootstrap.lock"
flock -n 9

# Check only public deployment identity. Never read WordPress configuration or DB.
php -r '$s=json_decode(file_get_contents($argv[1]),true);exit(is_array($s)&&($s["site_id"]??0)===23048&&($s["repository"]??"")==="angsm111-dot/lombardgorzow"&&in_array($s["origin"]??"",["https://nowa.lombardgorzow.com","https://lombardgorzow.com"],true)?0:1);' "$sezam_web/deployment-status.json"

sezam_deploy="$(mktemp "$sezam_state/production-deploy.XXXXXXXX")"
sezam_status_tmp=''
trap 'rm -f -- "$sezam_deploy" "$sezam_status_tmp"' EXIT

sezam_status() {
  sezam_directory "$sezam_web"
  [ ! -L "$sezam_web/sezam-deployment-check.txt" ]
  if [ -e "$sezam_web/sezam-deployment-check.txt" ]; then sezam_file "$sezam_web/sezam-deployment-check.txt"; fi
  sezam_status_tmp="$(mktemp "$sezam_web/sezam-status.XXXXXXXX")"
  echo "$1" >"$sezam_status_tmp"
  if [ "$2" = yes ]; then sed -n '/^Deployment stopped: /p' "$sezam_state/deployment.log" | head -c 4096 >>"$sezam_status_tmp"; fi
  chmod 644 "$sezam_status_tmp"
  mv -f -- "$sezam_status_tmp" "$sezam_web/sezam-deployment-check.txt"
}

if ! { curl --proto =https --tlsv1.2 -fsS --connect-timeout 20 --max-time 60 "https://raw.githubusercontent.com/angsm111-dot/lombardgorzow/$sezam_commit/scripts/deploy-jdm.php" -o "$sezam_deploy" && echo "$sezam_sha256  $sezam_deploy" | sha256sum --check --status && php -l "$sezam_deploy"; } >"$sezam_state/deployment.log" 2>&1; then
  sezam_status 'Stopped: production deployment pin, download or syntax check failed.' no
  exit 1
fi
if ! php "$sezam_deploy" "--profile=$sezam_profile" >"$sezam_state/deployment.log" 2>&1; then
  sezam_status "Stopped during $sezam_profile deployment; inspect deployment-status.json and retry safely." yes
  exit 1
fi
sezam_status "Published SEZAM $sezam_profile site 23048. See deployment-status.json for the commit and profile." no
