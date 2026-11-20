#!/bin/sh
# Read-only preflight inspection for site 23048. Writes only a temporary private
# PHP script and sanitized public JSON; no installation or key access.
set -eu
PATH=/usr/local/bin:/usr/bin:/bin
export PATH
[ "$#" = 0 ]
[ "$(id -un)" = vvictgzv ]
[ "$(id -u)" != 0 ]
[ "$HOME" = /home/vvictgzv ]
[ "$(getent passwd vvictgzv | cut -d: -f6)" = "$HOME" ]
[ "$(readlink -f "$HOME")" = "$HOME" ]
umask 077
sezam_state="$HOME/.sezam-nowa-deploy"
[ ! -L "$sezam_state" ]
[ "$(find "$sezam_state" -maxdepth 0 -type d -user vvictgzv -print)" = "$sezam_state" ]
[ -z "$(find "$sezam_state" -maxdepth 0 -perm /077 -print)" ]
sezam_control="$(mktemp -d "$sezam_state/catalog-diagnostic.XXXXXXXX")"
[ ! -L "$sezam_control" ]
[ "$(find "$sezam_control" -maxdepth 0 -type d -user vvictgzv -print)" = "$sezam_control" ]
[ "$(stat -c %a "$sezam_control")" = 700 ]
sezam_cleanup() {
  [ ! -L "$sezam_control" ] && [ "$(find "$sezam_control" -maxdepth 0 -type d -user vvictgzv -print)" = "$sezam_control" ] && rm -rf -- "$sezam_control"
}
trap sezam_cleanup EXIT
# Avoid passing multiword PHP code through JDM's whitespace-splitting launcher.
cat >"$sezam_control/diagnostic.php" <<'SEZAM_DIAGNOSTIC'
<?php
declare(strict_types=1);
ini_set('display_errors','0');ini_set('log_errors','0');
$home='/home/vvictgzv';$uid=posix_geteuid();$web=$home.'/public_html';
function insist(bool $ok): void { if(!$ok)throw new RuntimeException('preflight_failed'); }
function owned(string $path,bool $directory=false): void {
    global $uid;insist(!is_link($path)&&($directory?is_dir($path):is_file($path))&&fileowner($path)===$uid);
}
function privateDirectory(string $path): void { owned($path,true);insist((fileperms($path)&0077)===0); }
function data(string $path): array { owned($path);insist(filesize($path)<=65536);$value=json_decode((string)file_get_contents($path),true);insist(is_array($value));return $value; }
// Do not write even the diagnostic unless this is the verified static site.
try {
    owned($web,true);$identity=data($web.'/deployment-status.json');
    insist(($identity['site_id']??null)===23048&&($identity['repository']??'')==='angsm111-dot/lombardgorzow');
} catch(Throwable) { fwrite(STDERR,"Diagnostic site identity check failed.\n");exit(1); }
$result=['site_id'=>23048,'diagnostic'=>'catalog-preflight-v1','checked_at'=>gmdate('c'),'result'=>'stopped','stage'=>'start','checks'=>[
    'cli_sapi'=>PHP_SAPI==='cli','open_basedir_enabled'=>ini_get('open_basedir')!=='','stdin_path_readable'=>@is_readable('/dev/stdin')]];
$stage='state_directory';
try {
    $state=$home.'/.sezam-nowa-deploy';privateDirectory($state);
    $stage='preparation_marker';owned($state.'/static-preparation-23048.txt');insist(trim((string)file_get_contents($state.'/static-preparation-23048.txt'))==='Prepared SEZAM static site 23048');
    $stage='private_deployment_state';$private=data($state.'/deployed.json');
    foreach(['public'=>$identity,'private'=>$private] as $kind=>$status) {
        $stage=$kind.'_deployment_identity';
        insist(($status['site_id']??null)===23048&&($status['repository']??'')==='angsm111-dot/lombardgorzow'&&($status['branch']??'')==='work/sezam-kontakt-cennik');
        $stage=$kind.'_deployment_profile';$profile=$status['profile']??'';insist(in_array($profile,['preview','production'],true));
        $origin=$profile==='production'?'https://lombardgorzow.com':'https://nowa.lombardgorzow.com';
        insist(($status['origin']??'')===$origin&&($status['profile_fingerprint']??'')===hash('sha256',"sezam-deploy-v3\n".$profile."\n".$origin));
        insist(($status['status']??'')==='deployed'&&preg_match('/^[a-f0-9]{40}$/D',$status['commit']??'')===1);
    }
    $stage='deployment_states_match';insist($identity['commit']===$private['commit']&&$identity['profile_fingerprint']===$private['profile_fingerprint']);
    $stage='template_access';owned($web.'/assets',true);owned($web.'/assets/sales-template.html');
    $template=(string)file_get_contents($web.'/assets/sales-template.html');
    $stage='template_contents';insist(strlen($template)<=1000000&&str_contains($template,'<!-- SEZAM_SALES_TEMPLATE_V1 -->')&&substr_count($template,'<main id="main">')===1&&substr_count($template,'</main>')===1&&!str_contains($template,'<?'));
    $base=$home.'/private/lombardgorzow-catalog';
    foreach(['private_parent'=>$home.'/private','catalog_root'=>$base,'catalog_data'=>$base.'/data','catalog_releases'=>$base.'/releases'] as $name=>$directory) {
        $stage=$name.'_symlink';insist(!is_link($directory));
        $result['checks'][$name.'_exists']=file_exists($directory);
        if(file_exists($directory)) {
            $stage=$name.'_ownership';owned($directory,true);
            $stage=$name.'_permissions';insist((fileperms($directory)&0077)===0);
        }
    }
    $stage='catalog_tree';
    if(is_dir($base)) {
        $iterator=new RecursiveIteratorIterator(new RecursiveDirectoryIterator($base,FilesystemIterator::SKIP_DOTS),RecursiveIteratorIterator::SELF_FIRST);
        foreach($iterator as $item) {
            $path=$item->getPathname();
            if($path===$base.'/current'&&is_link($path)) {
                $target=readlink($path);insist(is_string($target)&&preg_match('~^releases/[a-f0-9]{40}$~D',$target)===1);privateDirectory($base.'/'.$target);
            } else { owned($path,$item->isDir());insist((fileperms($path)&0077)===0); }
        }
    }
    // Inspect key-file metadata only; never read authorized_keys or any key.
    foreach(['ssh_directory'=>$home.'/.ssh','authorized_keys_metadata'=>$home.'/.ssh/authorized_keys'] as $name=>$path) {
        $stage=$name;insist(!is_link($path));if(file_exists($path))owned($path,is_dir($path));
    }
    $stage='receiver_disabled';
    if(is_file($base.'/config.json'))insist((data($base.'/config.json')['enabled']??null)===false);
    $result['result']='ready';$stage='complete';
} catch(Throwable) { /* The fixed stage is the entire public error detail. */ }
$result['stage']=$stage;
$target=$web.'/sezam-catalog-preflight-check.json';
if(is_link($target)||(file_exists($target)&&(!is_file($target)||fileowner($target)!==$uid)))exit(1);
$temp=tempnam($web,'sezam-catalog-preflight.');if($temp===false)exit(1);
try { if(file_put_contents($temp,json_encode($result,JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n")===false||!chmod($temp,0644)||!rename($temp,$target))exit(1); }
finally { if(is_file($temp))unlink($temp); }
echo json_encode(['result'=>$result['result'],'stage'=>$stage],JSON_THROW_ON_ERROR)."\n";
exit($result['result']==='ready'?0:1);
SEZAM_DIAGNOSTIC
[ ! -L "$sezam_control/diagnostic.php" ]
[ "$(find "$sezam_control/diagnostic.php" -maxdepth 0 -type f -user vvictgzv -print)" = "$sezam_control/diagnostic.php" ]
[ "$(stat -c %a "$sezam_control/diagnostic.php")" = 600 ]
php "$sezam_control/diagnostic.php"
