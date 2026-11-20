<?php
declare(strict_types=1);
namespace LombardCatalog;

const PRIVATE_ROOT = '/home/vvictgzv/private/lombardgorzow-catalog';
const PUBLIC_ROOT = '/home/vvictgzv/public_html';
const PUBLIC_STUB = "<?php\ndeclare(strict_types=1);\nrequire '/home/vvictgzv/private/lombardgorzow-catalog/current/router.php';\n";
const PUBLIC_STUB_SHA256 = '0386468c7f866cdf66936701f0e8ddd45a962d450f8efc0e3411e61099945233';
const CATEGORIES = ['bizuteria'=>'Biżuteria','pierscionki'=>'Pierścionki','zegarki'=>'Zegarki','telefony'=>'Telefony','laptopy'=>'Laptopy','tablety'=>'Tablety','fotografia'=>'Fotografia','konsole'=>'Konsole','elektronarzedzia'=>'Elektronarzędzia','rowery'=>'Rowery'];
const STATUSES = ['in_stock','reserved','sold','unavailable'];

final class Failure extends \RuntimeException {}
function fail(string $code): never { throw new Failure($code); }
function safeFile(string $path): void {
    if (is_link($path) || (file_exists($path) && !is_file($path))) fail('unsafe_path');
}
function directory(string $path, int $mode=0700): void {
    if (is_link($path) || (file_exists($path) && !is_dir($path))) fail('unsafe_path');
    if (!is_dir($path) && !mkdir($path,$mode)) fail('directory_unavailable');
    if (!chmod($path,$mode)) fail('permissions_failed');
}
function atomic(string $path, string $bytes, int $mode=0600): void {
    safeFile($path);
    if (!is_dir(dirname($path)) || is_link(dirname($path))) fail('unsafe_path');
    $temp=dirname($path).'/.catalog-write-'.bin2hex(random_bytes(8));
    $stream=fopen($temp,'xb');
    if (!$stream) fail('write_failed');
    try {
        if (!chmod($temp,$mode)) fail('permissions_failed');
        $offset=0;
        while ($offset<strlen($bytes)) {
            $written=fwrite($stream,substr($bytes,$offset));
            if ($written===false || $written===0) fail('write_failed');
            $offset+=$written;
        }
        if (!fflush($stream)) fail('write_failed');
        if (function_exists('fsync') && !fsync($stream)) fail('write_failed');
        fclose($stream); $stream=null;
        if (!rename($temp,$path)) fail('write_failed');
    } finally {
        if (is_resource($stream)) fclose($stream);
        if (is_file($temp)) unlink($temp);
    }
}
function jsonRead(string $path, array $fallback=[]): array {
    safeFile($path);
    if (!is_file($path)) return $fallback;
    if (filesize($path)>50000000) fail('data_invalid');
    $data=json_decode((string)file_get_contents($path),true,128,JSON_THROW_ON_ERROR);
    if (!is_array($data)) fail('data_invalid');
    return $data;
}
function jsonWrite(string $path, array $value): void {
    atomic($path,json_encode($value,JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n");
}
function locked(string $path, callable $work): mixed {
    safeFile($path); $handle=fopen($path,'c');
    if (!$handle || !flock($handle,LOCK_EX|LOCK_NB)) fail('busy');
    try { chmod($path,0600); return $work(); }
    finally { flock($handle,LOCK_UN); fclose($handle); }
}
function deploymentLocked(App $app, callable $work): mixed {
    $dir=dirname($app->public).'/.sezam-nowa-deploy';directory($dir);
    $path=$dir.'/deployment.lock';safeFile($path);$handle=fopen($path,'c');
    if (!$handle || !flock($handle,LOCK_EX)) fail('deployment_busy');
    try { return $work(); } finally { flock($handle,LOCK_UN);fclose($handle); }
}
function validDate(mixed $value): string {
    if (!is_string($value) || !preg_match('/^\d{4}-\d{2}-\d{2}$/D',$value)) fail('source_date');
    $date=\DateTimeImmutable::createFromFormat('!Y-m-d',$value,new \DateTimeZone('UTC'));
    if (!$date || $date->format('Y-m-d')!==$value || $value>gmdate('Y-m-d',time()+86400)) fail('source_date');
    return $value;
}
final class App {
    public function __construct(public readonly string $base=PRIVATE_ROOT, public readonly string $public=PUBLIC_ROOT) {
        if (is_link($base) || !is_dir($base) || is_link($public) || !is_dir($public)) fail('installation_unavailable');
    }
    public function config(): array {
        $c=jsonRead($this->base.'/config.json',['enabled'=>false,'transport'=>'ssh-push','interval_minutes'=>30]);
        if (!is_bool($c['enabled']??null) || ($c['transport']??'')!=='ssh-push' || ($c['interval_minutes']??null)!==30) fail('configuration_invalid');
        return $c;
    }
    public function snapshot(): array {
        $s=jsonRead($this->base.'/data/catalog.json',['products'=>[],'source_checked_on'=>null,'synced_at'=>null]);
        if (!is_array($s['products']??null) || !array_is_list($s['products']) || array_key_exists('owner_id',$s)) fail('catalog_invalid');
        return $s;
    }
}
function validateProductFields(array $p): void {
    $slug=$p['slug']??null;
    if (!is_string($slug) || strlen($slug)>230 || !preg_match('/^[a-z0-9]+(?:-[a-z0-9]+)*$/D',$slug) || isset(CATEGORIES[$slug])) fail('product_invalid');
    if (!isset(CATEGORIES[$p['category']??'']) || !in_array($p['status']??null,STATUSES,true)) fail('product_invalid');
    foreach (['name'=>1000,'description'=>100000] as $field=>$limit) {
        if (!is_string($p[$field]??null) || trim($p[$field])==='' || strlen($p[$field])>$limit || !preg_match('//u',$p[$field])) fail('product_invalid');
    }
    if ((!is_int($p['price']??null) && !is_float($p['price']??null) && !is_string($p['price']??null)) || !is_numeric($p['price']) || !is_finite((float)$p['price']) || (float)$p['price']<=0 || (float)$p['price']>1000000000) fail('product_invalid');
    if (!is_string($p['source_id']??null) || !preg_match('/^ID[a-z0-9]+$/iD',$p['source_id'])) fail('product_invalid');
    $url=is_string($p['source_url']??null)?parse_url($p['source_url']):false;
    if (!is_array($url) || ($url['scheme']??'')!=='https' || ($url['host']??'')!=='www.olx.pl' || isset($url['user']) || isset($url['pass']) || isset($url['port']) || isset($url['fragment']) || !str_starts_with($url['path']??'','/')) fail('product_invalid');
    validDate($p['checked_on']??null);
    if (isset($p['price_valid_until']) && $p['price_valid_until']!=='') {
        if (!is_string($p['price_valid_until']) || !preg_match('/^\d{4}-\d{2}-\d{2}$/D',$p['price_valid_until'])) fail('product_invalid');
    }
    if (isset($p['olx_id']) && (!is_scalar($p['olx_id']) || !ctype_digit((string)$p['olx_id']))) fail('product_invalid');
}
function validateProducts(App $app, array $products): void {
    if (!array_is_list($products) || count($products)>50000) fail('catalog_invalid');
    $ids=[];$slugs=[];$olxIds=[];
    foreach ($products as $p) {
        if (!is_array($p)) fail('product_invalid');
        validateProductFields($p);
        $id=strtoupper($p['source_id']);
        if (isset($ids[$id]) || isset($slugs[$p['slug']])) fail('catalog_duplicate');
        $ids[$id]=true;$slugs[$p['slug']]=true;
        if (isset($p['olx_id'])) { if (isset($olxIds[(string)$p['olx_id']])) fail('catalog_duplicate'); $olxIds[(string)$p['olx_id']]=true; }
        $images=$p['images']??null;
        if (!is_array($images) || !array_is_list($images) || !$images || count($images)>30 || !is_string($p['image']??null) || !in_array($p['image'],$images,true)) fail('image_invalid');
        foreach ($images as $image) {
            if (!is_string($image) || !preg_match('~^/assets/sales-feed-[a-f0-9]{64}\.(?:jpg|png|webp)$~D',$image) || is_link($app->public.$image) || !is_file($app->public.$image)) fail('image_invalid');
        }
    }
}
function publicPaths(array $products): array {
    $paths=['na-sprzedaz/index.php','integracje/katalog/oferty/index.php','integracje/katalog/mapa/index.php'];
    foreach (array_merge(array_keys(CATEGORIES),array_column($products,'slug')) as $slug) $paths[]='na-sprzedaz/'.$slug.'/index.php';
    return array_values(array_unique($paths));
}
function ensurePublicStub(App $app,string $relative): void {
    if (!preg_match('~^(?:na-sprzedaz/(?:[a-z0-9]+(?:-[a-z0-9]+)*/)?|integracje/katalog/(?:oferty|mapa)/)index\.php$~D',$relative)) fail('route_invalid');
    $parent=$app->public;
    foreach (explode('/',dirname($relative)) as $part) { $parent.='/'.$part; directory($parent,0755); }
    $path=$app->public.'/'.$relative; safeFile($path);
    if (is_file($path) && !hash_equals(PUBLIC_STUB_SHA256,hash_file('sha256',$path))) fail('public_entry_conflict');
    if (!is_file($path)) atomic($path,PUBLIC_STUB,0644);
}
function removeManagedPlaceholder(App $app): void {
    $path=$app->public.'/na-sprzedaz/index.html'; safeFile($path);
    if (is_file($path)) {
        $html=(string)file_get_contents($path);
        if (!str_contains($html,'<!-- SEZAM_SALES_PLACEHOLDER -->')) fail('public_entry_conflict');
        if (!unlink($path)) fail('public_entry_conflict');
    }
}
function publishCatalog(App $app,array $snapshot): void {
    deploymentLocked($app,function()use($app,$snapshot): void { publishCatalogUnlocked($app,$snapshot); });
}
function publishCatalogUnlocked(App $app,array $snapshot): void {
    validateProducts($app,$snapshot['products']);
    renderCatalog($app,$snapshot);
    foreach (array_keys(CATEGORIES) as $route) renderCatalog($app,$snapshot,$route);
    foreach ($snapshot['products'] as $p) renderCatalog($app,$snapshot,$p['slug']);
    // Every route is ready before the single shared snapshot becomes visible.
    foreach (publicPaths($snapshot['products']) as $path) ensurePublicStub($app,$path);
    $placeholder=$app->public.'/na-sprzedaz/index.html';
    if (is_file($placeholder) && !str_contains((string)file_get_contents($placeholder),'<!-- SEZAM_SALES_PLACEHOLDER -->')) fail('public_entry_conflict');
    $current=$app->base.'/data/catalog.json';
    if (is_file($current)) atomic($app->base.'/data/catalog.previous.json',(string)file_get_contents($current));
    jsonWrite($app->base.'/data/public-paths.json',['schema'=>1,'sha256'=>PUBLIC_STUB_SHA256,'paths'=>publicPaths($snapshot['products'])]);
    removeManagedPlaceholder($app);
    // No fallible publication work follows the atomic switch of live data.
    jsonWrite($current,$snapshot);
}
