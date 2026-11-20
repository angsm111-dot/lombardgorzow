<?php
declare(strict_types=1);
namespace LombardCatalog;
// Run only from a reviewed, SHA-pinned private deployment payload. No network I/O.
if (PHP_SAPI!=='cli') { http_response_code(404);exit; }
umask(0077);ini_set('display_errors','0');ini_set('log_errors','0');
require_once __DIR__.'/core.php';

function installSenderKey(string $home,string $publicKey,string $phpBinary,string $base,bool $dryRun=false): void {
    $key=trim($publicKey);
    if (!preg_match('/^ssh-ed25519 ([A-Za-z0-9+\/]{68})(?: [A-Za-z0-9_.@-]{1,100})?$/D',$key,$m) || !str_starts_with($phpBinary,'/') || preg_match('/[\r\n\x00]/',$phpBinary.$base)) fail('sender_key_invalid');
    $blob=base64_decode($m[1],true);
    if ($blob===false || strlen($blob)!==51 || substr($blob,0,19)!==pack('N',11).'ssh-ed25519'.pack('N',32)) fail('sender_key_invalid');
    $dir=$home.'/.ssh';if(is_link($dir) || (file_exists($dir) && !is_dir($dir)))fail('unsafe_path');
    if (!$dryRun) directory($dir);$file=$dir.'/authorized_keys';safeFile($file);
    $previous=is_file($file)?(string)file_get_contents($file):'';
    if (strlen($previous)>1000000) fail('authorized_keys_invalid');
    $command=escapeshellarg($phpBinary).' '.escapeshellarg($base.'/current/cli.php').' --receive';
    $line='restrict,command="'.str_replace(['\\','"'],['\\\\','\\"'],$command).'" ssh-ed25519 '.$m[1].' sezam-public-catalog-lombardgorzow';
    foreach (preg_split('/\r?\n/',$previous) as $existing) {
        if (preg_match('/(?:^|\s)ssh-ed25519\s+'.preg_quote($m[1],'/').'(?:\s|$)/',$existing)) {
            if ($existing!==$line) fail('sender_key_conflict');
            if (!$dryRun) chmod($file,0600);return;
        }
    }
    if (!$dryRun) atomic($file,rtrim($previous,"\r\n").($previous!==''?"\n":"").$line."\n");
}
function installPackage(string $source,string $release,?string $senderKey,bool $enable=false,string $base=PRIVATE_ROOT,string $public=PUBLIC_ROOT): array {
    if (!preg_match('/^[a-f0-9]{40}$/D',$release) || !is_dir($source) || is_link($source) || !is_dir($public) || is_link($public)) fail('install_arguments');
    $home=dirname($public);$private=dirname($base);
    if ($private!==$home.'/private' || basename($base)!=='lombardgorzow-catalog') fail('install_arguments');
    directory($private);directory($base);directory($base.'/data');directory($base.'/releases');
    $app=new App($base,$public);
    return locked($app->base.'/data/sync.lock',function()use($app,$source,$release,$senderKey,$enable,$home): array {
      return deploymentLocked($app,function()use($app,$source,$release,$senderKey,$enable,$home): array {
        return locked($app->base.'/data/install.lock',function()use($app,$source,$release,$senderKey,$enable,$home): array {
            $files=['core.php','receive.php','cli.php','renderer.php','router.php'];
            $bundle=[];
            foreach ($files as $file) {
                $path=$source.'/'.$file;safeFile($path);
                if (!is_file($path) || filesize($path)>250000) fail('install_payload_missing');
                $bundle[$file]=(string)file_get_contents($path);
                if (!str_starts_with($bundle[$file],'<?php')) fail('install_payload_invalid');
                token_get_all($bundle[$file],TOKEN_PARSE);
            }
            if (!hash_equals(PUBLIC_STUB_SHA256,hash('sha256',PUBLIC_STUB))) fail('bootstrap_invalid');
            validateProducts($app,$app->snapshot()['products']);
            $template=$app->public.'/assets/sales-template.html';safeFile($template);
            if (!is_file($template)) fail('template_unavailable');
            $html=(string)file_get_contents($template);
            if (!str_contains($html,'<!-- SEZAM_SALES_TEMPLATE_V1 -->') || !str_contains($html,'<main id="main">') || str_contains($html,'<?')) fail('template_invalid');
            $placeholder=$app->public.'/na-sprzedaz/index.html';safeFile($placeholder);
            if (is_file($placeholder) && !str_contains((string)file_get_contents($placeholder),'<!-- SEZAM_SALES_PLACEHOLDER -->')) fail('public_entry_conflict');
            foreach (publicPaths($app->snapshot()['products']) as $path) {
                $entry=$app->public.'/'.$path;safeFile($entry);
                if (is_file($entry) && !hash_equals(PUBLIC_STUB_SHA256,hash_file('sha256',$entry))) fail('public_entry_conflict');
            }
            if ($senderKey!==null) installSenderKey($home,$senderKey,PHP_BINARY,$app->base,true);
            $current=$app->base.'/current';
            if (file_exists($current) && !is_link($current)) fail('release_pointer_conflict');
            $oldPointer=is_link($current)?readlink($current):null;
            if ($oldPointer!==null && !preg_match('~^releases/[a-f0-9]{40}$~D',$oldPointer)) fail('release_pointer_conflict');
            $destination=$app->base.'/releases/'.$release;directory($destination);
            foreach ($bundle as $name=>$bytes) {
                $path=$destination.'/'.$name;safeFile($path);
                if (is_file($path) && hash_file('sha256',$path)!==hash('sha256',$bytes)) fail('release_immutable');
                if (!is_file($path)) atomic($path,$bytes);
            }
            $saved=[];
            foreach (['config.json','public-site.json','template.html','catalog-active.json','data/catalog.json','data/public-paths.json'] as $file) {
                $path=$app->base.'/'.$file;safeFile($path);$saved[$path]=is_file($path)?(string)file_get_contents($path):null;
            }
            if ($senderKey!==null) {$path=$home.'/.ssh/authorized_keys';safeFile($path);$saved[$path]=is_file($path)?(string)file_get_contents($path):null;}
            $oldPlaceholder=is_file($placeholder)?(string)file_get_contents($placeholder):null;
            $newStubs=[];foreach(publicPaths($app->snapshot()['products']) as $path)if(!is_file($app->public.'/'.$path))$newStubs[]=$app->public.'/'.$path;
            try {
            // Runtime data and owner enable/disable state survive every update.
            if (!is_file($app->base.'/config.json')) jsonWrite($app->base.'/config.json',['enabled'=>false,'transport'=>'ssh-push','interval_minutes'=>30]);
            $config=$app->config();if ($enable) { $config['enabled']=true;jsonWrite($app->base.'/config.json',$config); }
            if (!is_file($app->base.'/public-site.json')) jsonWrite($app->base.'/public-site.json',['origin'=>'https://lombardgorzow.com','name'=>'Lombard SEZAM','address'=>'ul. Pocztowa 11, 66-400 Gorzów Wielkopolski','whatsapp'=>'48601775146','olx_profile'=>'https://www.olx.pl/oferty/uzytkownik/G2XGE/']);
            atomic($app->base.'/template.html',$html);
            require_once $source.'/renderer.php';
            renderCatalog($app,$app->snapshot());
            $tmp=$app->base.'/.current-'.bin2hex(random_bytes(8));
            if (!symlink('releases/'.$release,$tmp) || !rename($tmp,$current)) fail('release_pointer_failed');
            foreach (publicPaths($app->snapshot()['products']) as $path) ensurePublicStub($app,$path);
            if (!is_file($app->base.'/data/catalog.json')) jsonWrite($app->base.'/data/catalog.json',['products'=>[],'source_checked_on'=>null,'synced_at'=>null]);
            removeManagedPlaceholder($app);
            if ($senderKey!==null) installSenderKey($home,$senderKey,PHP_BINARY,$app->base);
            jsonWrite($app->base.'/catalog-active.json',['schema'=>1,'site_id'=>23048,'bootstrap_sha256'=>PUBLIC_STUB_SHA256]);
            jsonWrite($app->base.'/data/public-paths.json',['schema'=>1,'sha256'=>PUBLIC_STUB_SHA256,'paths'=>publicPaths($app->snapshot()['products'])]);
            return ['result'=>'installed','release'=>$release,'enabled'=>$app->config()['enabled'],'bootstrap_sha256'=>PUBLIC_STUB_SHA256,'private_runtime'=>true,'php'=>PHP_VERSION];
            } catch (\Throwable $error) {
                $rollbackOk=true;
                try {
                    if ($oldPointer===null) {if(is_link($current)&&!unlink($current))fail('rollback');}
                    else {$restore=$app->base.'/.restore-'.bin2hex(random_bytes(8));if(!symlink($oldPointer,$restore)||!rename($restore,$current))fail('rollback');}
                } catch(\Throwable){$rollbackOk=false;}
                foreach($saved as $path=>$bytes)try{if($bytes===null){if(is_file($path)&&!unlink($path))fail('rollback');}else atomic($path,$bytes);}catch(\Throwable){$rollbackOk=false;}
                foreach($newStubs as $path)try{if(is_file($path)&&hash_equals(PUBLIC_STUB_SHA256,hash_file('sha256',$path))&&!unlink($path))fail('rollback');}catch(\Throwable){$rollbackOk=false;}
                if($oldPlaceholder!==null)try{atomic($placeholder,$oldPlaceholder,0644);}catch(\Throwable){$rollbackOk=false;}
                if(!$rollbackOk)fail('install_rollback_failed');
                throw $error;
            }
        });
      });
    });
}
if (realpath($_SERVER['SCRIPT_FILENAME']??'')===__FILE__) {
    try {
        $args=getopt('',['source:','release:','sender-key:','enable']);
        if (array_diff(array_keys($args),['source','release','sender-key','enable']) || !isset($args['release'])) fail('install_arguments');
        $senderKey=null;
        if (isset($args['sender-key'])) { safeFile($args['sender-key']);if (!is_file($args['sender-key']) || filesize($args['sender-key'])>2048) fail('sender_key_invalid');$senderKey=(string)file_get_contents($args['sender-key']); }
        $result=installPackage($args['source']??__DIR__,$args['release'],$senderKey,array_key_exists('enable',$args));
        echo json_encode($result,JSON_THROW_ON_ERROR)."\n";
    } catch (\Throwable $error) { echo json_encode(['result'=>'error','reason'=>$error instanceof Failure?$error->getMessage():'install_error'],JSON_THROW_ON_ERROR)."\n";exit(1); }
}
