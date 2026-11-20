#!/bin/sh
# Reviewed receiver release; pin the dedicated public key separately before
# --activate-key. No private key belongs here.
# Site 23048 only; no WordPress, domain, DNS, SSL or cron changes.
set -eu
PATH=/usr/local/bin:/usr/bin:/bin
export PATH
if [ "$#" != 1 ]; then echo 'Use --prepare or --activate-key.' >&2; exit 2; fi
case "$1" in --prepare|--activate-key) sezam_action="$1";; *) echo 'Use --prepare or --activate-key.' >&2; exit 2;; esac
sezam_release=d511eacaaa42946dd15cbb667aa0712f37bb61db
sezam_sender_key=UNPINNED
sezam_sender_key_sha256=UNPINNED
if [ "${#sezam_release}" != 40 ]; then echo 'Catalog release is unpinned; nothing executed.' >&2; exit 2; fi
case "$sezam_release" in *[!0-9a-f]*) echo 'Invalid catalog release pin.' >&2; exit 2;; esac
if [ "$sezam_action" = --activate-key ]; then
  if [ "${#sezam_sender_key_sha256}" != 64 ]; then echo 'Sender public key is unpinned; nothing executed.' >&2; exit 2; fi
  case "$sezam_sender_key_sha256" in *[!0-9a-f]*) echo 'Invalid sender public-key pin.' >&2; exit 2;; esac
fi

[ "$(id -un)" = vvictgzv ]
[ "$(id -u)" != 0 ]
[ "$HOME" = /home/vvictgzv ]
[ "$(getent passwd vvictgzv | cut -d: -f6)" = "$HOME" ]
[ "$(readlink -f "$HOME")" = "$HOME" ]
umask 077
sezam_state="$HOME/.sezam-nowa-deploy"
sezam_web="$HOME/public_html"
sezam_private="$HOME/private"
sezam_catalog="$sezam_private/lombardgorzow-catalog"

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
for sezam_guard in "$sezam_state/catalog-install.lock" "$sezam_web/sezam-catalog-install-check.json"; do
  [ ! -L "$sezam_guard" ]
  if [ -e "$sezam_guard" ]; then sezam_file "$sezam_guard"; fi
done
exec 8>"$sezam_state/catalog-install.lock"
flock -n 8

# Fail before network or installation unless the catalog-aware static deployer
# has already published this account and the reviewed template is available.
php -f /dev/stdin -- "$sezam_action" "$sezam_release" <<'SEZAM_PREFLIGHT'
<?php
declare(strict_types=1);
ini_set('display_errors','0');
$home='/home/vvictgzv'; $uid=posix_geteuid();
function insist(bool $ok): void { if (!$ok) { fwrite(STDERR,"Catalog preflight failed; no installation performed.\n"); exit(1); } }
function owned(string $path, bool $directory=false): void {
    global $uid;
    insist(!is_link($path) && ($directory?is_dir($path):is_file($path)) && fileowner($path)===$uid);
}
function privateDirectory(string $path): void { owned($path,true); insist((fileperms($path)&0077)===0); }
function data(string $path): array { owned($path); insist(filesize($path)<=65536); $value=json_decode((string)file_get_contents($path),true); insist(is_array($value)); return $value; }
$state=$home.'/.sezam-nowa-deploy'; $web=$home.'/public_html';
privateDirectory($state); owned($web,true);
owned($state.'/static-preparation-23048.txt');
insist(trim((string)file_get_contents($state.'/static-preparation-23048.txt'))==='Prepared SEZAM static site 23048');
$public=data($web.'/deployment-status.json'); $private=data($state.'/deployed.json');
foreach([$public,$private] as $status) {
    insist(($status['site_id']??null)===23048 && ($status['repository']??'')==='angsm111-dot/lombardgorzow' && ($status['branch']??'')==='work/sezam-kontakt-cennik');
    $profile=$status['profile']??''; insist(in_array($profile,['preview','production'],true));
    $origin=$profile==='production'?'https://lombardgorzow.com':'https://nowa.lombardgorzow.com';
    insist(($status['origin']??'')===$origin && ($status['profile_fingerprint']??'')===hash('sha256',"sezam-deploy-v3\n".$profile."\n".$origin));
    insist(($status['status']??'')==='deployed' && preg_match('/^[a-f0-9]{40}$/D',$status['commit']??'')===1);
}
insist($public['commit']===$private['commit'] && $public['profile_fingerprint']===$private['profile_fingerprint']);
owned($web.'/assets',true); owned($web.'/assets/sales-template.html');
$template=(string)file_get_contents($web.'/assets/sales-template.html');
insist(strlen($template)<=1000000 && str_contains($template,'<!-- SEZAM_SALES_TEMPLATE_V1 -->') && substr_count($template,'<main id="main">')===1 && substr_count($template,'</main>')===1 && !str_contains($template,'<?'));
$base=$home.'/private/lombardgorzow-catalog';
foreach([$home.'/private',$base,$base.'/data',$base.'/releases'] as $directory) {
    insist(!is_link($directory)); if(file_exists($directory)) privateDirectory($directory);
}
if(is_dir($base)) {
    $iterator=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($base,FilesystemIterator::SKIP_DOTS),RecursiveIteratorIterator::SELF_FIRST);
    foreach($iterator as $item) {
        $path=$item->getPathname();
        if($path===$base.'/current' && is_link($path)) {
            $target=readlink($path); insist(is_string($target) && preg_match('~^releases/[a-f0-9]{40}$~D',$target)===1); privateDirectory($base.'/'.$target);
        } else { owned($path,$item->isDir()); insist((fileperms($path)&0077)===0); }
    }
}
foreach([$home.'/.ssh',$home.'/.ssh/authorized_keys'] as $path) {
    insist(!is_link($path)); if(file_exists($path)) owned($path,is_dir($path));
}
if($argv[1]==='--prepare' && is_file($base.'/config.json')) insist((data($base.'/config.json')['enabled']??null)===false);
if($argv[1]==='--activate-key') {
    $marker=data($base.'/catalog-active.json');
    insist($marker===['schema'=>1,'site_id'=>23048,'bootstrap_sha256'=>'0386468c7f866cdf66936701f0e8ddd45a962d450f8efc0e3411e61099945233']);
    insist(is_link($base.'/current') && readlink($base.'/current')==='releases/'.$argv[2]);
}
SEZAM_PREFLIGHT

if [ ! -e "$sezam_private" ]; then mkdir -m 700 "$sezam_private"; fi
sezam_directory "$sezam_private"
sezam_stage="$(mktemp -d "$sezam_private/catalog-install.XXXXXXXX")"
sezam_directory "$sezam_stage"
[ "$(stat -c %a "$sezam_stage")" = 700 ]
sezam_success=false
sezam_report() {
  # The public proof contains selected public metadata only, never logs, paths,
  # key material, configuration values or arbitrary installer output.
  php -f /dev/stdin -- "$sezam_action" "$sezam_release" "$sezam_success" <<'SEZAM_REPORT'
<?php
declare(strict_types=1);
ini_set('display_errors','0');
$base='/home/vvictgzv/private/lombardgorzow-catalog'; $web='/home/vvictgzv/public_html'; $uid=posix_geteuid();
if(is_link($web)||!is_dir($web)||fileowner($web)!==$uid)exit(1);
$out=['site_id'=>23048,'action'=>$argv[1]==='--prepare'?'prepare':'activate-key','release'=>$argv[2],'result'=>$argv[3]==='true'?'ready':'stopped','checked_at'=>gmdate('c')];
if($argv[3]==='true') {
    foreach(['config.json','data/catalog.json','data/web-check.json'] as $relative) {
        $file=$base.'/'.$relative;
        if(is_link($file)||!is_file($file)||fileowner($file)!==$uid||filesize($file)>50000000)continue;
        $data=json_decode((string)file_get_contents($file),true);if(!is_array($data))continue;
        if($relative==='config.json' && is_bool($data['enabled']??null))$out['enabled']=$data['enabled'];
        if($relative==='data/catalog.json' && is_array($data['products']??null))$out['products']=count($data['products']);
        if($relative==='data/web-check.json') {
            $out['web_private_access']=($data['private_access']??false)===true;
            $out['web_sapi']=in_array($data['sapi']??'', ['fpm-fcgi','cgi-fcgi','apache2handler','litespeed'],true)?$data['sapi']:'unconfirmed';
            $out['web_open_basedir_enabled']=($data['open_basedir_enabled']??false)===true;
        }
    }
}
$target=$web.'/sezam-catalog-install-check.json';
if(is_link($target)||(file_exists($target)&&(!is_file($target)||fileowner($target)!==$uid)))exit(1);
$temp=tempnam($web,'sezam-catalog-proof.');if($temp===false)exit(1);
try { if(file_put_contents($temp,json_encode($out,JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n")===false||!chmod($temp,0644)||!rename($temp,$target))exit(1); }
finally { if(is_file($temp))unlink($temp); }
SEZAM_REPORT
}
sezam_finish() {
  sezam_exit="$?"
  trap - EXIT
  sezam_report || sezam_exit=1
  # Remove only this script's uniquely-created, guarded staging directory.
  if sezam_directory "$sezam_stage"; then rm -rf -- "$sezam_stage"; else sezam_exit=1; fi
  exit "$sezam_exit"
}
trap sezam_finish EXIT

cat >"$sezam_stage/SHA256SUMS" <<'SEZAM_HASHES'
aeeef07ae4c81152c6337f1c6191be58121c5b6b118a3f65811d4fe668b63e20  core.php
10b6c13254041dc2bafeb548317f7c412f5ab9bb62855dd5d39e979bc47e77d1  receive.php
5cdd9205e3138049306ae0dd8c8d6c65394c79de797efee8ee38dfb77287d09f  cli.php
9d5f64a2ae871a2d949184b7f92f75c07a4520058f5f24eda922eecf822238f6  install.php
fbfd8a96e29ce3e00332a0467a77b370f43a5671fb07601fbbb9f3bb585ed9ef  renderer.php
1494c64f451b5e05db4949e836a4b9af3dd91f893db035e648e4d447ea6edadb  router.php
SEZAM_HASHES
sezam_log="$sezam_state/catalog-install.log"
[ ! -L "$sezam_log" ]
if [ -e "$sezam_log" ]; then sezam_file "$sezam_log"; fi
: >"$sezam_log"
chmod 600 "$sezam_log"
for sezam_name in core receive cli install renderer router; do
  curl --proto =https --tlsv1.2 -fsS --connect-timeout 20 --max-time 60 --max-filesize 250000 "https://raw.githubusercontent.com/angsm111-dot/lombardgorzow/$sezam_release/integrations/catalog-receiver/$sezam_name.php" -o "$sezam_stage/$sezam_name.php" >>"$sezam_log" 2>&1
done
(cd "$sezam_stage" && sha256sum --check --status SHA256SUMS) >>"$sezam_log" 2>&1
for sezam_name in core receive cli install renderer router; do php -l "$sezam_stage/$sezam_name.php" >>"$sezam_log" 2>&1; done
if [ "$sezam_action" = --activate-key ]; then
  printf '%s\n' "$sezam_sender_key" >"$sezam_stage/sender.pub"
  echo "$sezam_sender_key_sha256  $sezam_stage/sender.pub" | sha256sum --check --status >>"$sezam_log" 2>&1
  php "$sezam_stage/install.php" "--source=$sezam_stage" "--release=$sezam_release" "--sender-key=$sezam_stage/sender.pub" --enable >>"$sezam_log" 2>&1
else
  php "$sezam_stage/install.php" "--source=$sezam_stage" "--release=$sezam_release" >>"$sezam_log" 2>&1
fi
php "$sezam_catalog/current/cli.php" --check >>"$sezam_log" 2>&1
sezam_success=true
echo 'Catalog stage completed; see sezam-catalog-install-check.json.'
