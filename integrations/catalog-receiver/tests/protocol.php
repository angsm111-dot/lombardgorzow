<?php
declare(strict_types=1);
namespace LombardCatalog;
require dirname(__DIR__).'/core.php';
require dirname(__DIR__).'/renderer.php';
require dirname(__DIR__).'/receive.php';
require dirname(__DIR__).'/install.php';
set_exception_handler(function(\Throwable $error):void{fwrite(STDERR,$error->getMessage()." at ".$error->getFile().':'.$error->getLine()."\n");exit(1);});

$checks=0;
function check(bool $ok,string $label): void {global $checks;if(!$ok)throw new \RuntimeException('FAILED: '.$label);$checks++;}
function rejects(callable $fn,string $label): void {try{$fn();}catch(\Throwable){check(true,$label);return;}check(false,$label);}
function stream(array $frames) { $s=fopen('php://temp','w+');foreach($frames as $frame)fwrite($s,json_encode($frame,JSON_THROW_ON_ERROR)."\n");rewind($s);return $s; }
function ingest(App $app,array $rows,string $bytes,bool $complete=true,?array $override=null): array {
    $digest=hash('sha256',$bytes);$exists=false;
    foreach(['png','jpg','webp']as$ext)if(is_file($app->public.'/assets/sales-feed-'.$digest.'.'.$ext))$exists=true;
    $frames=[$override??['format'=>'sezam-public-offers-v1','source'=>'sezam.com.pl','checked_on'=>'2026-11-20','currency'=>'PLN','count'=>count($rows),'products'=>$rows]];
    if($rows&&!$exists)$frames[]=['sha256'=>$digest,'data'=>base64_encode($bytes)];
    if($complete)$frames[]=['complete'=>true];
    $input=stream($frames);$out=fopen('php://temp','w+');
    try{receiveCatalog($app,$input,$out);rewind($out);return array_map(fn($line)=>json_decode($line,true,64,JSON_THROW_ON_ERROR),array_filter(explode("\n",stream_get_contents($out))));}
    finally{fclose($input);fclose($out);}
}
function removeTree(string $path):void {if(is_link($path)||is_file($path)){unlink($path);return;}foreach(scandir($path)as$name)if($name!=='.'&&$name!=='..')removeTree($path.'/'.$name);rmdir($path);}
$home=sys_get_temp_dir().'/catalog-fixtures-'.bin2hex(random_bytes(6));
mkdir($home,0700);mkdir($home.'/private',0700);mkdir($home.'/public_html',0755);mkdir($home.'/public_html/assets',0755);
$base=$home.'/private/lombardgorzow-catalog';mkdir($base,0700);mkdir($base.'/data',0700);
$app=new App($base,$home.'/public_html');
$template='<!doctype html><html lang="pl"><head><meta charset="utf-8"><title>Na sprzedaż</title><meta name="description" content="Katalog"><meta name="robots" content="noindex"><link rel="canonical" href="https://lombardgorzow.com/na-sprzedaz/"></head><body><!-- SEZAM_SALES_TEMPLATE_V1 --><header>SEZAM</header><main id="main"><h1>Na sprzedaż</h1></main><footer>Kontakt</footer></body></html>';
atomic($app->public.'/assets/sales-template.html',$template,0644);
jsonWrite($base.'/config.json',['enabled'=>true,'transport'=>'ssh-push','interval_minutes'=>30]);
jsonWrite($base.'/public-site.json',['origin'=>'https://lombardgorzow.com','name'=>'Lombard SEZAM','address'=>'ul. Pocztowa 11, 66-400 Gorzów Wielkopolski','whatsapp'=>'48601775146','olx_profile'=>'https://www.olx.pl/oferty/uzytkownik/G2XGE/']);
$_SERVER['HTTP_HOST']='lombardgorzow.com';
$png=base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aC0QAAAAASUVORK5CYII=');
$digest=hash('sha256',$png);
$p=['slug'=>'pierscionek-testowy-idabc1','name'=>'Pierścionek <script>alert(1)</script>','category'=>'bizuteria','status'=>'in_stock','source_id'=>'IDabc1','source_url'=>'https://www.olx.pl/d/oferta/pierscionek-IDabc1.html','description'=>'Opis <img src=x onerror=alert(1)>','price'=>1234.50,'checked_on'=>'2026-11-20','images'=>[$digest,$digest]];
try {
    check(hash('sha256',PUBLIC_STUB)===PUBLIC_STUB_SHA256,'fixed bootstrap digest');
    mkdir($app->public.'/na-sprzedaz',0755);atomic($app->public.'/na-sprzedaz/index.html','<!-- SEZAM_SALES_PLACEHOLDER -->',0644);
    $replies=ingest($app,[$p],$png);
    check($replies[0]===['ready'=>'sezam-public-offers-v1'],'protocol greeting');
    check($replies[1]===['missing'=>[$digest]],'deduplicated gallery transfer');
    check(end($replies)['result']==='ok'&&end($replies)['count']===1,'receipt count');
    check(!is_file($app->public.'/na-sprzedaz/index.html'),'managed placeholder removed');
    $s=$app->snapshot();check(count($s['products'])===1&&count($s['products'][0]['images'])===2,'full gallery retained');
    check($s['source_checked_on']==='2026-11-20','source date retained');
    check(hash_file('sha256',$app->public.'/na-sprzedaz/'.$p['slug'].'/index.php')===PUBLIC_STUB_SHA256,'stable public stub');
    $html=renderCatalog($app,$s,$p['slug']);
    check(substr_count($html,'<h1')===1,'one product h1');
    check(!str_contains($html,'<script>alert(1)</script>')&&str_contains($html,'&lt;script&gt;'),'title escaped');
    check(!str_contains($html,'<img src=x'),'description escaped');
    check(str_contains($html,'https://lombardgorzow.com/na-sprzedaz/'.$p['slug'].'/'),'own canonical');
    check(str_contains(str_replace('\\/','/',$html),'https://schema.org/InStock'),'available schema');
    check(matchesCategory($s['products'][0],'pierscionki'),'ring filter');
    check(substr_count($html,'aria-label="Zdjęcie ')===2,'full gallery markup');
    $oldHash=hash_file('sha256',$base.'/data/catalog.json');
    $bad=$p;$bad['source_url']='https://evil.example/';rejects(fn()=>ingest($app,[$bad],$png),'untrusted source url rejected');
    rejects(fn()=>ingest($app,[$p,$p],$png),'duplicate ids rejected');
    rejects(fn()=>ingest($app,[$p],$png,false),'truncated transfer rejected');
    $bad=$p;$bad['category']='unknown';rejects(fn()=>ingest($app,[$bad],$png),'unknown category rejected');
    $bad=$p;$bad['checked_on']='2026-02-31';rejects(fn()=>ingest($app,[$bad],$png),'invalid date rejected');
    $bad=$p;$bad['owner_id']='secret';rejects(fn()=>ingest($app,[$bad],$png),'unexpected private field rejected');
    $bad=$p;$bad['images']=['bad'];rejects(fn()=>ingest($app,[$bad],$png),'invalid digest rejected');
    check(hash_file('sha256',$base.'/data/catalog.json')===$oldHash,'failed imports preserve exact lastgood');
    $renamed=$p;$renamed['name']='Nowy tytuł';$renamed['slug']='nowy-tytul';ingest($app,[$renamed],$png);
    check($app->snapshot()['products'][0]['slug']===$p['slug'],'title changes preserve old slug');
    $receipt=ingest($app,[],$png);$s=$app->snapshot();
    check(end($receipt)['count']===0&&end($receipt)['active_count']===0,'complete empty source receipt');
    check(count($s['products'])===1&&$s['products'][0]['status']==='unavailable','ended item retained unavailable');
    check(str_contains(str_replace('\\/','/',renderCatalog($app,$s,$p['slug'])),'https://schema.org/OutOfStock'),'ended schema');
    $manifest=['format'=>'sezam-public-offers-v1','source'=>'sezam.com.pl','checked_on'=>'2026-11-19','currency'=>'PLN','count'=>0,'products'=>[]];
    rejects(fn()=>ingest($app,[],$png,true,$manifest),'older source rejected');
    $c=$app->config();$c['enabled']=false;jsonWrite($base.'/config.json',$c);
    $reply=ingest($app,[$p],$png);check($reply===[['result'=>'disabled']],'disabled receiver performs no import');
    // Public-key installer preserves unrelated keys and accepts no shell options from input.
    $key='ssh-ed25519 '.base64_encode(pack('N',11).'ssh-ed25519'.pack('N',32).str_repeat('x',32));
    mkdir($home.'/.ssh',0700);atomic($home.'/.ssh/authorized_keys',"# existing owner key is preserved\n");
    installSenderKey($home,$key,'/usr/bin/php',$base);
    $keys=(string)file_get_contents($home.'/.ssh/authorized_keys');
    check(str_starts_with($keys,'# existing owner key is preserved'),'owner authorized_keys preserved');
    check(str_contains($keys,'restrict,command=')&&str_contains($keys,' --receive'),'restricted forced command');
    installSenderKey($home,$key,'/usr/bin/php',$base);check((string)file_get_contents($home.'/.ssh/authorized_keys')===$keys,'key install idempotent');
    rejects(fn()=>installSenderKey($home,'command="sh" '.$key,'/usr/bin/php',$base),'untrusted key options rejected');
    rejects(fn()=>installSenderKey($home,$key,'/usr/bin/php-other',$base),'same key different command conflict');
    check(str_contains(renderSitemap($app,$s),$p['slug']),'unavailable URL kept in map');
    $catalogBefore=hash_file('sha256',$base.'/data/catalog.json');
    $installed=installPackage(dirname(__DIR__),str_repeat('a',40),null,false,$base,$app->public);
    check($installed['result']==='installed'&&!$installed['enabled'],'installer preserves disabled owner setting');
    check(readlink($base.'/current')==='releases/'.str_repeat('a',40),'immutable version pointer installed');
    check(hash_file('sha256',$base.'/data/catalog.json')===$catalogBefore,'installer preserves live catalog');
    check(jsonRead($base.'/catalog-active.json')===['schema'=>1,'site_id'=>23048,'bootstrap_sha256'=>PUBLIC_STUB_SHA256],'deployment guard marker exact');
    check((fileperms($base.'/catalog-active.json')&0077)===0,'marker has no group or public permissions');
    installPackage(dirname(__DIR__),str_repeat('b',40),null,false,$base,$app->public);
    check(readlink($base.'/current')==='releases/'.str_repeat('b',40),'code update selects new release');
    check(hash_file('sha256',$base.'/data/catalog.json')===$catalogBefore,'code update preserves lastgood data');
    $category=$app->public.'/na-sprzedaz/fotografia';unlink($category.'/index.php');rmdir($category);mkdir($home.'/outside',0700);symlink($home.'/outside',$category);
    rejects(fn()=>installPackage(dirname(__DIR__),str_repeat('c',40),null,true,$base,$app->public),'unsafe route aborts install transaction');
    check(readlink($base.'/current')==='releases/'.str_repeat('b',40),'failed install restores version pointer');
    check(!$app->config()['enabled'],'failed install restores enabled state');
    check(hash_file('sha256',$base.'/data/catalog.json')===$catalogBefore,'failed install preserves catalog');
    check(jsonRead($base.'/catalog-active.json')['bootstrap_sha256']===PUBLIC_STUB_SHA256,'failed install preserves valid guard marker');
    echo "Catalog receiver: $checks checks passed; no network or real offers used.\n";
} finally {removeTree($home);}
