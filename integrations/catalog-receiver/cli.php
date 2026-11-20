<?php
declare(strict_types=1);
namespace LombardCatalog;
if (PHP_SAPI!=='cli') { http_response_code(404);exit; }
umask(0077);ini_set('display_errors','0');ini_set('log_errors','0');
require __DIR__.'/core.php';
require __DIR__.'/renderer.php';
require __DIR__.'/receive.php';
$app=null;
try {
    $app=new App();$action=$argv[1]??'';
    if ($action==='--receive') {
        if (getenv('SSH_ORIGINAL_COMMAND')!=='receive-public-catalog-v1' || count($argv)!==2) fail('command_rejected');
        stream_set_timeout(STDIN,120);receiveCatalog($app,STDIN,STDOUT);exit(0);
    }
    if (getenv('SSH_CONNECTION')!==false && getenv('SSH_ORIGINAL_COMMAND')!==false) fail('command_rejected');
    if ($action==='--check') {
        $s=$app->snapshot();validateProducts($app,$s['products']);
        echo json_encode(['result'=>'ready','enabled'=>$app->config()['enabled'],'transport'=>'ssh-push','interval_minutes'=>30,'products'=>count($s['products']),'status'=>jsonRead($app->base.'/data/status.json'),'web_check'=>jsonRead($app->base.'/data/web-check.json')],JSON_THROW_ON_ERROR)."\n";exit;
    }
    if ($action==='--enable' || $action==='--disable') {
        locked($app->base.'/data/sync.lock',function()use($app,$action){$c=$app->config();$c['enabled']=$action==='--enable';jsonWrite($app->base.'/config.json',$c);});
        echo json_encode(['result'=>'ok','enabled'=>$app->config()['enabled']],JSON_THROW_ON_ERROR)."\n";exit;
    }
    fail('command_rejected');
} catch (\Throwable $error) {
    $code=$error instanceof Failure ? $error->getMessage() : 'receiver_error';
    echo json_encode(['result'=>'error','reason'=>$code],JSON_THROW_ON_ERROR)."\n";exit(1);
}
