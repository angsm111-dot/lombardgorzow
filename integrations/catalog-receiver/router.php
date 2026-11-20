<?php
declare(strict_types=1);
namespace LombardCatalog;
ini_set('display_errors','0');
ini_set('log_errors','0');
require_once __DIR__.'/core.php';
require_once __DIR__.'/renderer.php';

header('Cache-Control: no-store, max-age=0');
header('X-Content-Type-Options: nosniff');
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if (!in_array($method,['GET','HEAD'],true)) { http_response_code(405); header('Allow: GET, HEAD'); exit; }
$path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH);
$json = $path === '/integracje/katalog/oferty/';
$map = $path === '/integracje/katalog/mapa/';
header('Content-Type: '.($json ? 'application/json' : ($map ? 'application/xml' : 'text/html')).'; charset=utf-8');
if ($json || !in_array(strtolower(explode(':',$_SERVER['HTTP_HOST'] ?? '')[0]),['lombardgorzow.com','www.lombardgorzow.com'],true)) header('X-Robots-Tag: noindex, follow');
try {
    $app = new App('/home/vvictgzv/private/lombardgorzow-catalog','/home/vvictgzv/public_html');
    $snapshot = $app->snapshot();
    // Private proof of the real web SAPI; never expose diagnostic configuration publicly.
    try {
        $proof = $app->base.'/data/web-check.json';
        if (!is_file($proof) || filemtime($proof) < time()-3600) jsonWrite($proof,['checked_at'=>gmdate('c'),'sapi'=>PHP_SAPI,'open_basedir_enabled'=>ini_get('open_basedir') !== '', 'private_access'=>true]);
    } catch (\Throwable $ignored) { /* Diagnostics must not interrupt a valid catalogue. */ }
    if ($json) {
        validateProducts($app,$snapshot['products']);
        $body = json_encode(['products'=>publicProducts($snapshot['products']),'source_checked_on'=>catalogReadDate($snapshot),'categories'=>CATEGORIES],JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_HEX_TAG);
    } elseif ($map) $body = renderSitemap($app,$snapshot);
    elseif (is_string($path) && preg_match('~^/na-sprzedaz/(?:([a-z0-9]+(?:-[a-z0-9]+)*)/)?$~D',$path,$match)) $body = renderCatalog($app,$snapshot,$match[1] ?? '');
    else throw new \RuntimeException('not_found');
    if ($method !== 'HEAD') echo $body;
} catch (\Throwable $error) {
    $missing = $error->getMessage() === 'not_found';
    http_response_code($missing ? 404 : 503);
    if ($method !== 'HEAD') {
        if ($json) echo '{"error":"catalog_unavailable"}';
        elseif ($map) echo '<?xml version="1.0"?><error>catalog_unavailable</error>';
        else echo '<!doctype html><html lang="pl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Katalog SEZAM</title><main><h1>'.($missing?'Nie znaleziono przedmiotu':'Katalog jest chwilowo niedostępny').'</h1><p><a href="/na-sprzedaz/">Wróć do katalogu</a> lub <a href="https://www.olx.pl/oferty/uzytkownik/G2XGE/">sprawdź nasze ogłoszenia OLX</a>.</p></main></html>';
    }
}
