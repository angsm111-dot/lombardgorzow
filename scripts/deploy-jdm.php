#!/usr/bin/env php
<?php
declare(strict_types=1);

/* Run only from JDM's native cron for the isolated HTML site. No credentials. */
const EXPECTED_ACCOUNT = 'vvictgzv';
const EXPECTED_SITE_ID = 23048;
const REPOSITORY = 'angsm111-dot/lombardgorzow';
const BRANCH = 'work/sezam-kontakt-cennik';
const PREVIEW_ORIGIN = 'https://nowa.lombardgorzow.com';
const PRODUCTION_ORIGIN = 'https://lombardgorzow.com';
const SITES_ORIGIN = 'https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site';
const TRANSFORM_REVISION = 'sezam-deploy-v3';
const FROZEN_MANIFEST_SHA256 = '03b8ad8d7b60f131caeac90801584570c6ee23921bd83aa63b22035c05d42cd6';
const MAX_DOWNLOAD = 67108864;
const MAX_EXPANDED = 67108864;
const MAX_FILE = 10485760;
const CATALOG_BOOTSTRAP_SHA256 = '0386468c7f866cdf66936701f0e8ddd45a962d450f8efc0e3411e61099945233';

function requireCondition(bool $condition, string $message): void {
    if (!$condition) { throw new RuntimeException($message); }
}

function deploymentProfile(string $name = 'preview'): array {
    requireCondition(in_array($name, ['preview', 'production'], true), 'Unknown deployment profile.');
    $origin = $name === 'production' ? PRODUCTION_ORIGIN : PREVIEW_ORIGIN;
    return ['name' => $name, 'origin' => $origin,
        'fingerprint' => hash('sha256', TRANSFORM_REVISION . "\n" . $name . "\n" . $origin)];
}

function profileFromArguments(array $arguments): array {
    requireCondition($arguments === [] || $arguments === ['--profile=preview'] || $arguments === ['--profile=production'], 'Only --profile=preview or --profile=production is accepted.');
    return deploymentProfile($arguments === ['--profile=production'] ? 'production' : 'preview');
}

function comparisonPath(string $relative): bool {
    return preg_match('~^(?:wersja-[^/]+/|porownanie(?:-wersji)?/|odwazne/|kolejne/|koncepcje/)~D', $relative) === 1
        || in_array($relative, ['404.html', 'assets/sales-template.html'], true);
}

function robotsText(array $profile, bool $catalogActive = false): string {
    return $profile['name'] === 'preview' ? "User-agent: *\nDisallow: /\n"
        : "User-agent: *\nAllow: /\nSitemap: " . $profile['origin'] . "/sitemap.xml\n"
            . ($catalogActive ? 'Sitemap: ' . $profile['origin'] . "/integracje/katalog/mapa/\n" : '');
}

function matchesDeployment(array $previous, string $sha, array $profile, bool $catalogActive = false): bool {
    return ($previous['commit'] ?? '') === $sha
        && ($previous['manifest_sha256'] ?? '') === FROZEN_MANIFEST_SHA256
        && ($previous['profile_fingerprint'] ?? '') === $profile['fingerprint']
        && ($previous['origin'] ?? '') === $profile['origin']
        && ($previous['catalog_runtime'] ?? false) === $catalogActive;
}

function ownedDirectory(string $path, int $uid, bool $create = false, int $mode = 0700): void {
    requireCondition(!is_link($path), 'Refusing symbolic-link directory.');
    $created = false;
    if (!file_exists($path) && $create) {
        requireCondition(mkdir($path, $mode), 'Cannot create deployment directory.');
        $created = true;
    }
    clearstatcache(true, $path);
    requireCondition(!is_link($path) && is_dir($path) && fileowner($path) === $uid, 'Directory ownership mismatch.');
    if ($created) { requireCondition(chmod($path, $mode), 'Cannot set deployment-directory permissions.'); }
}

function catalogRuntimeActive(string $home, int $uid): bool {
    $private = $home . '/private';
    $catalog = $private . '/lombardgorzow-catalog';
    requireCondition(!is_link($private) && !is_link($catalog), 'Symbolic link in catalog control path.');
    $marker = $catalog . '/catalog-active.json';
    requireCondition(!is_link($marker), 'Symbolic-link catalog marker.');
    if (!file_exists($marker)) { return false; }
    ownedDirectory($private, $uid);
    ownedDirectory($catalog, $uid);
    requireCondition((fileperms($catalog) & 0077) === 0, 'Catalog control directory must be private.');
    requireCondition(is_file($marker) && fileowner($marker) === $uid && filesize($marker) <= 1024 && (fileperms($marker) & 0077) === 0, 'Invalid catalog control marker.');
    $data = jsonObject(file_get_contents($marker));
    requireCondition(count($data) === 3 && ($data['schema'] ?? null) === 1 && ($data['site_id'] ?? null) === EXPECTED_SITE_ID
        && ($data['bootstrap_sha256'] ?? '') === CATALOG_BOOTSTRAP_SHA256, 'Catalog runtime identity differs from the reviewed installer.');
    return true;
}

function catalogStubPath(string $relative): bool {
    return safeRelative($relative) && (preg_match('~^na-sprzedaz/(?:[a-z0-9]+(?:-[a-z0-9]+)*/)?index\.php$~D', $relative) === 1
        || in_array($relative, ['integracje/katalog/oferty/index.php', 'integracje/katalog/mapa/index.php'], true));
}

function catalogPayloadPath(string $relative): bool {
    return strpos($relative, 'na-sprzedaz/') === 0 || strpos($relative, 'integracje/katalog/') === 0
        || strpos($relative, 'assets/sales-feed-') === 0;
}

function skipCatalogSource(string $relative, string $contents, bool $catalogActive): bool {
    if (!$catalogActive || !catalogPayloadPath($relative)) { return false; }
    requireCondition($relative === 'na-sprzedaz/index.html' && strpos($contents, '<!-- SEZAM_SALES_PLACEHOLDER -->') !== false,
        'Source archive collides with the active catalog runtime.');
    return true;
}

function guardWebRoot(string $home, string $web, int $uid, bool $catalogActive = false): void {
    ownedDirectory($home, $uid);
    ownedDirectory($web, $uid);
    requireCondition(realpath($web) === $home . '/public_html', 'Unexpected document root.');
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($web, FilesystemIterator::SKIP_DOTS),
        RecursiveIteratorIterator::SELF_FIRST
    );
    $count = 0;
    foreach ($iterator as $item) {
        requireCondition(++$count <= 5000, 'Unexpected document-root inventory.');
        $name = strtolower($item->getFilename());
        requireCondition(!$item->isLink(), 'Symbolic link found in document root.');
        requireCondition($item->getOwner() === $uid, 'Foreign-owned item in document root.');
        requireCondition(!in_array($name, ['wp-admin', 'wp-content', 'wp-includes', 'wp-config.php', 'wp-login.php'], true), 'WordPress detected; deployment forbidden.');
        if (preg_match('/\.(?:php\d*|phtml|phar)(?:\.|$)/i', $name)) {
            $relative = substr($item->getPathname(), strlen($web) + 1);
            requireCondition($catalogActive && $item->isFile() && catalogStubPath($relative)
                && hash_file('sha256', $item->getPathname()) === CATALOG_BOOTSTRAP_SHA256,
                'Unreviewed server-side script detected in document root.');
        }
    }
}

function safeRelative(string $path): bool {
    if ($path === '' || strlen($path) > 240 || strpos($path, '\\') !== false) { return false; }
    foreach (explode('/', $path) as $part) {
        if (!preg_match('/^[A-Za-z0-9][A-Za-z0-9._-]*$/D', $part) || $part === '.' || $part === '..') { return false; }
    }
    return true;
}

function safeSourcePath(string $path): bool {
    if ($path === '' || strlen($path) > 300 || strpos($path, '\\') !== false) { return false; }
    foreach (explode('/', $path) as $part) {
        if (!preg_match('/^[A-Za-z0-9._-]+$/D', $part) || $part === '.' || $part === '..') { return false; }
    }
    return true;
}

function staticPath(string $path): bool {
    return safeRelative($path)
        && !preg_match('/\.(?:php\d*|phtml|phar|cgi|pl|py|sh|bash|exe|dll)(?:\.|$)/i', $path)
        && in_array(strtolower(pathinfo($path, PATHINFO_EXTENSION)), ['html', 'css', 'js', 'json', 'xml', 'txt', 'svg', 'webp', 'png', 'jpg', 'jpeg', 'gif', 'avif', 'ico', 'woff', 'woff2', 'ttf', 'otf', 'pdf', 'mp4', 'webm'], true);
}

function request(string $url, int $limit, ?string $file = null, string $phase = 'download'): string {
    requireCondition(in_array($phase, ['ref', 'archive', 'download'], true), 'Unknown download phase.');
    $curl = curl_init($url);
    requireCondition($curl !== false, 'Cannot initialize HTTPS request.');
    $body = '';
    $bytes = 0;
    $handle = $file === null ? null : fopen($file, 'xb');
    requireCondition($file === null || $handle !== false, 'Cannot create download file.');
    curl_setopt_array($curl, [
        CURLOPT_USERAGENT => 'SEZAM-JDM-static-deployer/1.0',
        CURLOPT_HTTPHEADER => ['Accept: application/vnd.github+json'],
        CURLOPT_CONNECTTIMEOUT => 20,
        CURLOPT_TIMEOUT => 180,
        CURLOPT_PROTOCOLS => CURLPROTO_HTTPS,
        CURLOPT_REDIR_PROTOCOLS => CURLPROTO_HTTPS,
        CURLOPT_FOLLOWLOCATION => false,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_SSL_VERIFYHOST => 2,
        CURLOPT_WRITEFUNCTION => static function ($unused, string $chunk) use (&$body, &$bytes, $limit, $handle): int {
            $length = strlen($chunk);
            $bytes += $length;
            if ($bytes > $limit) { return 0; }
            if ($handle !== null) {
                $written = fwrite($handle, $chunk);
                return $written === false ? 0 : $written;
            }
            $body .= $chunk;
            return $length;
        },
    ]);
    $ok = curl_exec($curl);
    $status = (int) curl_getinfo($curl, CURLINFO_RESPONSE_CODE);
    $errno = curl_errno($curl);
    if ($handle !== null) { fclose($handle); }
    curl_close($curl);
    requireCondition($ok !== false && $status === 200 && $bytes <= $limit,
        sprintf('Public GitHub %s download failed (HTTP %d; curl %d; bytes %d; limit %d).', $phase, $status, $errno, $bytes, $limit));
    return $body;
}

function jsonObject(string $text): array {
    $decoded = json_decode($text, true, 64, JSON_THROW_ON_ERROR);
    requireCondition(is_array($decoded), 'Invalid JSON object.');
    return $decoded;
}

function frozenManifest(ZipArchive $zip, string $prefix): array {
    $entry = $zip->statName($prefix . 'config/frozen-versions.json');
    requireCondition(is_array($entry) && $entry['size'] <= 65536, 'Frozen manifest is missing or oversized.');
    $raw = $zip->getFromName($prefix . 'config/frozen-versions.json');
    requireCondition(is_string($raw) && hash('sha256', $raw) === FROZEN_MANIFEST_SHA256, 'Frozen manifest differs from the reviewed original.');
    $manifest = jsonObject($raw);
    $files = [];
    foreach ($manifest['versions'] as $version) {
        requireCondition($version['source_commit'] === '95518111742391729b954dc75710b88cdab8b71a', 'Unexpected frozen source version.');
        foreach ($version['files'] as $path => $hash) {
            requireCondition(strpos($path, 'dist/wersja-pierwotna/') === 0 && preg_match('/^[a-f0-9]{64}$/D', $hash) === 1, 'Invalid frozen manifest entry.');
            $relative = substr($path, 5);
            requireCondition(safeRelative($relative), 'Unsafe frozen path.');
            $files[$relative] = $hash;
        }
    }
    requireCondition(count($files) === 22, 'Expected exactly 22 frozen files.');
    return $files;
}

function verifyFrozen(string $directory, array $frozen): void {
    foreach ($frozen as $relative => $expected) {
        $path = $directory . '/' . $relative;
        requireCondition(is_file($path) && !is_link($path) && hash_file('sha256', $path) === $expected, 'Frozen version integrity check failed.');
    }
}

function transform(string $relative, string $contents, ?array $profile = null): string {
    $profile = $profile ?? deploymentProfile();
    if (strpos($relative, 'wersja-pierwotna/') === 0) { return $contents; }
    $extension = strtolower(pathinfo($relative, PATHINFO_EXTENSION));
    if (in_array($extension, ['html', 'xml', 'json'], true)) {
        $replacements = [];
        foreach ([SITES_ORIGIN, PREVIEW_ORIGIN, PRODUCTION_ORIGIN, 'https://www.lombardgorzow.com', 'https://www.nowa.lombardgorzow.com'] as $origin) {
            $replacements[$origin] = $profile['origin'];
            $replacements[str_replace('/', '\\/', $origin)] = str_replace('/', '\\/', $profile['origin']);
        }
        $contents = strtr($contents, $replacements);
    }
    if ($extension === 'html') {
        $pattern = '~<meta\b(?=[^>]*\bname\s*=\s*["\']robots["\'])[^>]*>\s*~i';
        preg_match_all($pattern, $contents, $existing);
        $directives = [];
        foreach ($existing[0] as $tag) {
            if (preg_match('~\bcontent\s*=\s*(["\'])(.*?)\1~i', $tag, $match)) {
                foreach (explode(',', html_entity_decode($match[2], ENT_QUOTES | ENT_HTML5, 'UTF-8')) as $value) {
                    $value = strtolower(trim($value));
                    if ($value !== '') { $directives[] = $value; }
                }
            }
        }
        $contents = preg_replace($pattern, '', $contents);
        if ($profile['name'] === 'preview') { $directives = ['noindex', 'nofollow']; }
        elseif (comparisonPath($relative)) {
            $directives = array_values(array_diff($directives, ['index', 'all']));
            if (!in_array('noindex', $directives, true) && !in_array('none', $directives, true)) { $directives[] = 'noindex'; }
            if (!in_array('follow', $directives, true) && !in_array('nofollow', $directives, true) && !in_array('none', $directives, true)) { $directives[] = 'follow'; }
        } elseif ($directives === []) { $directives = ['index', 'follow']; }
        // Production honors intentional source exclusions, including archival pages.
        // validateProfileFiles rejects any such page if it enters the public sitemap.
        $robots = htmlspecialchars(implode(',', array_unique($directives)), ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $contents = preg_replace('~<head\b[^>]*>~i', '$0' . "\n<meta name=\"robots\" content=\"$robots\">", $contents, 1, $count);
        requireCondition($count === 1, 'HTML document has no head.');
    }
    requireCondition(strpos($contents, SITES_ORIGIN) === false && strpos($contents, str_replace('/', '\\/', SITES_ORIGIN)) === false, 'Private Sites origin remains in export.');
    return $contents;
}

function validateProfileFiles(array $files, array $profile, bool $catalogActive = false): void {
    requireCondition(isset($files['sitemap.xml'], $files['index.html']), 'Homepage or sitemap is missing.');
    requireCondition(preg_match_all('~<loc>\s*([^<]+)\s*</loc>~i', $files['sitemap.xml'], $matches) > 0, 'Sitemap has no URLs.');
    foreach ($matches[1] as $raw) {
        $url = html_entity_decode(trim($raw), ENT_QUOTES | ENT_XML1, 'UTF-8');
        requireCondition(strpos($url, $profile['origin'] . '/') === 0, 'Sitemap origin differs from deployment profile.');
        $relative = ltrim((string) parse_url($url, PHP_URL_PATH), '/');
        if ($relative === '' || substr($relative, -1) === '/') { $relative .= 'index.html'; }
        $dynamicListing = $catalogActive && $relative === 'na-sprzedaz/index.html';
        requireCondition($dynamicListing || isset($files[$relative]), 'Sitemap points to a missing page.');
        if ($profile['name'] === 'production') {
            requireCondition(!comparisonPath($relative), 'Comparison page must not appear in the production sitemap.');
            requireCondition($dynamicListing || !preg_match('~<meta\b(?=[^>]*\bname\s*=\s*["\'](?:robots|googlebot)["\'])[^>]*\bcontent\s*=\s*["\'][^"\']*\b(?:noindex|none)\b[^"\']*["\'][^>]*>~i', $files[$relative]), 'Production sitemap contains a noindex page.');
        }
    }
}

function ensureParents(string $base, string $relative, int $uid, int $mode): void {
    $parts = explode('/', $relative);
    array_pop($parts);
    $current = $base;
    foreach ($parts as $part) {
        $current .= '/' . $part;
        ownedDirectory($current, $uid, true, $mode);
    }
}

function atomicWrite(string $base, string $relative, string $contents, int $uid, int $mode): void {
    requireCondition(safeRelative($relative), 'Unsafe publication path.');
    ensureParents($base, $relative, $uid, 0755);
    $target = $base . '/' . $relative;
    requireCondition(!is_link($target), 'Refusing symbolic-link publication target.');
    if (file_exists($target)) {
        requireCondition(is_file($target) && fileowner($target) === $uid, 'Publication target ownership/type mismatch.');
    }
    $temporary = dirname($target) . '/.sezam-' . bin2hex(random_bytes(8)) . '.tmp';
    $handle = fopen($temporary, 'xb');
    requireCondition($handle !== false, 'Cannot create atomic publication file.');
    try {
        requireCondition(fwrite($handle, $contents) === strlen($contents), 'Incomplete publication write.');
        requireCondition(fflush($handle), 'Cannot flush publication file.');
        fclose($handle);
        $handle = null;
        requireCondition(chmod($temporary, $mode), 'Cannot set publication permissions.');
        requireCondition(hash_file('sha256', $temporary) === hash('sha256', $contents), 'Publication checksum mismatch.');
        requireCondition(!is_link($target), 'Publication target became a symbolic link.');
        requireCondition(rename($temporary, $target), 'Atomic publication failed.');
    } finally {
        if (is_resource($handle)) { fclose($handle); }
        if (is_file($temporary)) { unlink($temporary); }
    }
}

function removePrivateStage(string $stage, string $state): void {
    requireCondition(dirname($stage) === $state && strpos(basename($stage), 'stage-') === 0 && !is_link($stage), 'Invalid cleanup scope.');
    if (!is_dir($stage)) { return; }
    $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($stage, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
    foreach ($iterator as $item) {
        if ($item->isDir() && !$item->isLink()) { rmdir($item->getPathname()); }
        else { unlink($item->getPathname()); }
    }
    rmdir($stage);
}

function main(array $arguments): void {
    $profile = profileFromArguments($arguments);
    requireCondition(PHP_SAPI === 'cli', 'This deployer is CLI-only.');
    requireCondition(extension_loaded('posix') && extension_loaded('curl') && class_exists('ZipArchive'), 'Required PHP CLI modules: posix, curl, zip.');
    $uid = posix_geteuid();
    $account = posix_getpwuid($uid);
    $expected = posix_getpwnam(EXPECTED_ACCOUNT);
    requireCondition(is_array($account) && is_array($expected) && $account['name'] === EXPECTED_ACCOUNT && $uid === $expected['uid'] && $uid !== 0, 'Wrong system account; deployment forbidden.');
    $home = realpath($account['dir']);
    requireCondition(is_string($home) && $home === $account['dir'] && !is_link($home), 'Unexpected account home.');
    if (getenv('HOME') !== false && getenv('HOME') !== '') {
        requireCondition(realpath(getenv('HOME')) === $home, 'Environment home/account mismatch.');
    }
    $web = $home . '/public_html';
    $catalogActive = catalogRuntimeActive($home, $uid);
    guardWebRoot($home, $web, $uid, $catalogActive);
    $state = $home . '/.sezam-nowa-deploy';
    ownedDirectory($state, $uid, true);
    $lockPath = $state . '/deployment.lock';
    requireCondition(!is_link($lockPath) && (!file_exists($lockPath) || fileowner($lockPath) === $uid), 'Unsafe lock file.');
    $lock = fopen($lockPath, 'c');
    requireCondition($lock !== false, 'Cannot open deployment lock.');
    if (!flock($lock, LOCK_EX | LOCK_NB)) { echo "Another deployment is running.\n"; return; }
    $stage = null;
    try {
        // The catalog installer shares deployment.lock while activating its marker.
        $catalogActive = catalogRuntimeActive($home, $uid);
        guardWebRoot($home, $web, $uid, $catalogActive);
        $ref = jsonObject(request('https://api.github.com/repos/' . REPOSITORY . '/git/ref/heads/' . BRANCH, 65536, null, 'ref'));
        $sha = $ref['object']['sha'] ?? '';
        requireCondition(($ref['ref'] ?? '') === 'refs/heads/' . BRANCH && ($ref['object']['type'] ?? '') === 'commit' && is_string($sha) && preg_match('/^[a-f0-9]{40}$/D', $sha) === 1, 'Unexpected GitHub branch response.');
        $stateFile = $state . '/deployed.json';
        requireCondition(!is_link($stateFile) && (!file_exists($stateFile) || (is_file($stateFile) && fileowner($stateFile) === $uid)), 'Unsafe deployment state.');
        if (is_file($stateFile)) {
            $previous = jsonObject(file_get_contents($stateFile));
            if (matchesDeployment($previous, $sha, $profile, $catalogActive)) {
                verifyFrozen($web, $previous['frozen_files']);
                requireCondition(is_file($web . '/index.html') && hash_file('sha256', $web . '/index.html') === $previous['index_sha256'], 'Previously deployed homepage was altered.');
                echo "Already deployed: $sha\n";
                return;
            }
        }
        $stage = $state . '/stage-' . $sha . '-' . bin2hex(random_bytes(4));
        ownedDirectory($stage, $uid, true);
        request('https://codeload.github.com/' . REPOSITORY . '/zip/' . $sha, MAX_DOWNLOAD, $stage . '/source.zip', 'archive');
        $zip = new ZipArchive();
        requireCondition($zip->open($stage . '/source.zip') === true, 'Cannot open source ZIP.');
        $prefix = 'lombardgorzow-' . $sha . '/';
        $frozen = frozenManifest($zip, $prefix);
        requireCondition($zip->numFiles <= 2000, 'Source ZIP has too many entries.');
        $files = [];
        $expanded = 0;
        $seen = [];
        for ($index = 0; $index < $zip->numFiles; $index++) {
            $entry = $zip->statIndex($index);
            requireCondition(is_array($entry), 'Invalid ZIP entry.');
            $name = $entry['name'];
            requireCondition(strpos($name, $prefix) === 0, 'ZIP root does not match pinned commit.');
            $inside = substr($name, strlen($prefix));
            if ($inside === '') { continue; }
            $clean = rtrim($inside, '/');
            requireCondition(safeSourcePath($clean), 'Unsafe source ZIP path.');
            if ($inside === 'dist/') { continue; }
            requireCondition(strpos($inside, 'dist/') !== 0 || safeRelative(rtrim(substr($inside, 5), '/')), 'Unsafe static ZIP path.');
            if (strpos($inside, 'dist/') !== 0 || substr($inside, -1) === '/') { continue; }
            $relative = substr($inside, 5);
            requireCondition(staticPath($relative), 'Non-static payload in dist; deployment forbidden.');
            requireCondition(!isset($seen[$relative]), 'Duplicate static ZIP path.');
            $seen[$relative] = true;
            requireCondition($zip->getExternalAttributesIndex($index, $system, $attributes), 'Cannot inspect ZIP entry type.');
            $type = ($attributes >> 16) & 0170000;
            requireCondition($type === 0 || $type === 0100000, 'Non-regular static ZIP entry.');
            requireCondition($entry['size'] <= MAX_FILE && ($expanded += $entry['size']) <= MAX_EXPANDED, 'Expanded static files exceed limits.');
            $contents = $zip->getFromIndex($index);
            requireCondition(is_string($contents) && strlen($contents) === $entry['size'], 'Incomplete static ZIP entry.');
            if (skipCatalogSource($relative, $contents, $catalogActive)) { continue; } // Never hide the managed index.php.
            if (strpos($relative, 'wersja-pierwotna/') === 0) {
                requireCondition(isset($frozen[$relative]) && hash('sha256', $contents) === $frozen[$relative], 'Unexpected or changed frozen file.');
            }
            $files[$relative] = transform($relative, $contents, $profile);
        }
        $zip->close();
        requireCondition(count($files) > 0 && isset($files['index.html'], $files['wersja-obecna/index.html'], $files['wersja-pierwotna/index.html']), 'Required homepage variants are missing.');
        foreach ($frozen as $relative => $hash) {
            requireCondition(isset($files[$relative]) && hash('sha256', $files[$relative]) === $hash, 'Frozen file missing from source ZIP.');
        }
        $files['robots.txt'] = robotsText($profile, $catalogActive);
        unset($files['deployment-status.json']);
        validateProfileFiles($files, $profile, $catalogActive);
        requireCondition(catalogRuntimeActive($home, $uid) === $catalogActive, 'Catalog activation changed during deployment.');
        guardWebRoot($home, $web, $uid, $catalogActive);
        /* Validate all destination paths before publishing the first file. */
        foreach (array_merge(array_keys($files), ['deployment-status.json']) as $relative) {
            $current = $web;
            $parts = explode('/', $relative);
            foreach ($parts as $position => $part) {
                $current .= '/' . $part;
                requireCondition(!is_link($current), 'Symbolic link in publication path.');
                if (file_exists($current)) {
                    requireCondition(fileowner($current) === $uid, 'Foreign-owned publication path.');
                    requireCondition($position === count($parts) - 1 ? is_file($current) : is_dir($current), 'Publication path has an unexpected file/directory type.');
                }
            }
        }
        uksort($files, static function (string $a, string $b): int {
            $weight = static function (string $path): int {
                if ($path === 'index.html') { return 3; }
                if (basename($path) === 'index.html') { return 2; }
                return pathinfo($path, PATHINFO_EXTENSION) === 'html' ? 1 : 0;
            };
            return ($weight($a) <=> $weight($b)) ?: strcmp($a, $b);
        });
        foreach ($files as $relative => $contents) { atomicWrite($web, $relative, $contents, $uid, 0644); }
        verifyFrozen($web, $frozen);
        $public = ['status' => 'deployed', 'site_id' => EXPECTED_SITE_ID, 'origin' => $profile['origin'], 'profile' => $profile['name'], 'profile_fingerprint' => $profile['fingerprint'], 'catalog_runtime' => $catalogActive, 'repository' => REPOSITORY, 'branch' => BRANCH, 'commit' => $sha, 'deployed_at' => gmdate('c'), 'files' => count($files), 'frozen_files_verified' => count($frozen)];
        atomicWrite($web, 'deployment-status.json', json_encode($public, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n", $uid, 0644);
        $private = $public + ['manifest_sha256' => FROZEN_MANIFEST_SHA256, 'frozen_files' => $frozen, 'index_sha256' => hash('sha256', $files['index.html'])];
        atomicWrite($state, 'deployed.json', json_encode($private, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n", $uid, 0600);
        echo "Deployed $sha to the isolated HTML site.\n";
    } finally {
        if ($stage !== null) { removePrivateStage($stage, $state); }
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}

try { main(array_slice($argv, 1)); }
catch (Throwable $error) {
    fwrite(STDERR, 'Deployment stopped: ' . $error->getMessage() . "\n");
    exit(1);
}
