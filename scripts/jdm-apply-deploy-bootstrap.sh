#!/bin/sh
# Reviewed one-time preparation plus repeatable static deployment for NEW site 23048.
set -eu
PATH=/usr/local/bin:/usr/bin:/bin
export PATH
[ "$(id -un)" = vvictgzv ]
[ "$(id -u)" != 0 ]
[ "$HOME" = /home/vvictgzv ]
[ "$(getent passwd vvictgzv | cut -d: -f6)" = "$HOME" ]
[ "$(readlink -f "$HOME")" = "$HOME" ]
umask 077
sezam_home="$HOME"
sezam_web="$sezam_home/public_html"
sezam_state="$sezam_home/.sezam-nowa-deploy"
sezam_holding="$sezam_home/.jdm-unused-installer-23048"
sezam_marker="$sezam_state/static-preparation-23048.txt"

sezam_directory() {
  [ ! -L "$1" ]
  [ "$(find "$1" -maxdepth 0 -type d -user vvictgzv -print)" = "$1" ]
}
sezam_file_guard() {
  [ ! -L "$1" ]
  if [ -e "$1" ]; then [ "$(find "$1" -maxdepth 0 -type f -user vvictgzv -print)" = "$1" ]; fi
}
sezam_directory "$sezam_home"
sezam_directory "$sezam_web"
[ ! -L "$sezam_state" ]
mkdir -p "$sezam_state"
sezam_directory "$sezam_state"
chmod 700 "$sezam_state"
for sezam_guard in "$sezam_state/preparation-bootstrap.lock" "$sezam_state/preparation.log" "$sezam_state/deployment.log" "$sezam_marker"; do sezam_file_guard "$sezam_guard"; done
exec 9>"$sezam_state/preparation-bootstrap.lock"
flock -n 9

# Only diagnostics created for this new site are moved; no project or WordPress file.
for sezam_name in sezam-bootstrap-check.txt sezam-server-check.txt sezam-download-check.txt sezam-inventory-check.txt sezam-content-check.txt sezam-wp-check.txt sezam-deployment-check.txt; do
  sezam_source="$sezam_web/$sezam_name"
  sezam_previous="$sezam_state/previous-$sezam_name"
  sezam_file_guard "$sezam_source"
  sezam_file_guard "$sezam_previous"
  if [ -f "$sezam_source" ]; then mv -f -- "$sezam_source" "$sezam_previous"; fi
done

sezam_prep="$(mktemp "$sezam_state/prepare.XXXXXXXX")"
sezam_deploy="$(mktemp "$sezam_state/deploy.XXXXXXXX")"
sezam_public_tmp=''
sezam_marker_tmp=''
trap 'rm -f -- "$sezam_prep" "$sezam_deploy" "$sezam_public_tmp" "$sezam_marker_tmp"' EXIT

sezam_status() {
  sezam_directory "$sezam_web"
  [ ! -e "$sezam_web/sezam-deployment-check.txt" ]
  [ ! -L "$sezam_web/sezam-deployment-check.txt" ]
  sezam_public_tmp="$(mktemp "$sezam_web/sezam-status.XXXXXXXX")"
  echo "$1" >"$sezam_public_tmp"
  if [ -n "$2" ]; then sed -n '/^Preparation stopped: /p;/^Deployment stopped: /p' "$2" | head -c 4096 >>"$sezam_public_tmp"; fi
  chmod 644 "$sezam_public_tmp"
  mv -- "$sezam_public_tmp" "$sezam_web/sezam-deployment-check.txt"
}

# Both executable scripts are downloaded, checksum-checked and linted BEFORE preparation.
if ! { curl --proto =https --tlsv1.2 -fsS --connect-timeout 20 --max-time 60 https://raw.githubusercontent.com/angsm111-dot/lombardgorzow/420e375b259964d2da941a62fe295ea5f7db8dcb/scripts/prepare-jdm-static.php -o "$sezam_prep" && echo "ada2b40b7e3152c3091eef85156fd465f1da4388555818388eb6233ccee0c5a3  $sezam_prep" | sha256sum --check --status && php -l "$sezam_prep"; } >"$sezam_state/preparation.log" 2>&1; then
  sezam_status 'Stopped: pinned preparation script download, checksum or syntax verification failed.' ''
  exit 1
fi
if ! { curl --proto =https --tlsv1.2 -fsS --connect-timeout 20 --max-time 60 https://raw.githubusercontent.com/angsm111-dot/lombardgorzow/420e375b259964d2da941a62fe295ea5f7db8dcb/scripts/deploy-jdm.php -o "$sezam_deploy" && echo "68aacc212a591703e8481d2ce27e23ca6b7d4e56a9f70aeb095eb3d5791219d4  $sezam_deploy" | sha256sum --check --status && php -l "$sezam_deploy"; } >"$sezam_state/deployment.log" 2>&1; then
  sezam_status 'Stopped: pinned deployment script download, checksum or syntax verification failed.' ''
  exit 1
fi

if [ -f "$sezam_marker" ]; then
  # A successful preparation is not repeated after an interrupted static-file deployment.
  [ "$(cat "$sezam_marker")" = 'Prepared SEZAM static site 23048' ]
  sezam_directory "$sezam_holding"
  [ "$(find "$sezam_holding" -maxdepth 0 -perm 0700 -print)" = "$sezam_holding" ]
else
  if ! php "$sezam_prep" --apply >"$sezam_state/preparation.log" 2>&1; then
    sezam_status 'Stopped during preparation; no deployment attempted.' "$sezam_state/preparation.log"
    exit 1
  fi
  sezam_directory "$sezam_holding"
  [ "$(find "$sezam_holding" -maxdepth 0 -perm 0700 -print)" = "$sezam_holding" ]
  sezam_marker_tmp="$(mktemp "$sezam_state/prepared.XXXXXXXX")"
  echo 'Prepared SEZAM static site 23048' >"$sezam_marker_tmp"
  mv -- "$sezam_marker_tmp" "$sezam_marker"
fi

# The deployer independently rejects all WordPress/PHP paths and verifies 22 frozen files.
if ! php "$sezam_deploy" >"$sezam_state/deployment.log" 2>&1; then
  sezam_status 'Stopped during static deployment; the next run may retry safely.' "$sezam_state/deployment.log"
  exit 1
fi
sezam_status 'Published isolated SEZAM HTML site 23048. See deployment-status.json for the commit.' ''
