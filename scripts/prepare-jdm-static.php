#!/usr/bin/env php
<?php
declare(strict_types=1);

/* NEW JDM site 23048 only; panel-confirmed awaiting setup on 2026-11-20. Default: checks only. */
const PREP_ACCOUNT = 'vvictgzv';
const PREP_HOME = '/home/vvictgzv';
const PREP_SITE_ID = 23048;
const PREP_ORIGIN = 'https://nowa.lombardgorzow.com';

function prepRequire(bool $ok, string $message): void {
    if (!$ok) { throw new RuntimeException($message); }
}

function prepDirectory(string $path, int $uid): void {
    prepRequire(!is_link($path) && is_dir($path) && fileowner($path) === $uid, 'Directory type or ownership mismatch.');
}

function prepJdmCacheDropIn(SplFileInfo $item, string $relative, int $uid): bool {
    /* Observed JDM-provisioned file in NEW site 23048; no other ownership exception. */
    return $relative === 'wp-content/object-cache.php'
        && !$item->isLink() && $item->isFile()
        && $item->getOwner() === 0 && $item->getGroup() === $uid
        && ($item->getPerms() & 07777) === 0750 && $item->getSize() === 49029;
}

function prepJdmOwnedFile(SplFileInfo $item, int $uid, int $bytes): bool {
    return !$item->isLink() && $item->isFile() && $item->getOwner() === $uid
        && ($item->getPerms() & 07777) === 0750 && $item->getSize() === $bytes;
}

function prepJdmMuPlugin(SplFileInfo $item, string $relative, int $uid): bool {
    if ($relative === 'wp-content/mu-plugins/jdm.php') { return prepJdmOwnedFile($item, $uid, 1116); }
    $base = 'wp-content/mu-plugins/jdm-plugins';
    if ($relative !== $base && strpos($relative, $base . '/') !== 0) { return false; }
    return !$item->isLink() && $item->getOwner() === $uid
        && ($item->isDir() || $item->isFile())
        && ($relative !== $base || ($item->isDir() && ($item->getPerms() & 07777) === 0750));
}

function prepInventory(string $directory, int $uid): array {
    prepDirectory($directory, $uid);
    $files = [];
    $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($directory, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::SELF_FIRST);
    foreach ($iterator as $item) {
        prepRequire(count($files) < 12000, 'Unexpectedly large scaffold.');
        $relative = substr($item->getPathname(), strlen($directory) + 1);
        $owned = $item->getOwner() === $uid || prepJdmCacheDropIn($item, $relative, $uid);
        prepRequire(!$item->isLink() && $owned && ($item->isDir() || $item->isFile()), 'Unexpected path type, symbolic link or owner.');
        $files[] = $relative;
    }
    return $files;
}

function prepScaffold(string $web, array $inventory): void {
    $allowedRoot = ['wp-admin', 'wp-includes', 'wp-content', 'index.php', 'license.txt', 'readme.html', 'wp-activate.php', 'wp-blog-header.php', 'wp-comments-post.php', 'wp-config.php', 'wp-config-sample.php', 'wp-cron.php', 'wp-links-opml.php', 'wp-load.php', 'wp-login.php', 'wp-mail.php', 'wp-settings.php', 'wp-signup.php', 'wp-trackback.php', 'xmlrpc.php', '.htaccess'];
    foreach ($inventory as $relative) {
        $top = explode('/', $relative)[0];
        prepRequire(in_array($top, $allowedRoot, true), 'Unexpected content in the new document root.');
        prepRequire(strpos($relative, 'wp-content/uploads/') !== 0, 'Uploads directory is not empty.');
        if (strpos($relative, 'wp-content/mu-plugins/') === 0) {
            prepRequire(prepJdmMuPlugin(new SplFileInfo($web . '/' . $relative), $relative, fileowner($web)), 'Unexpected JDM mu-plugin path or metadata: ' . $relative);
            continue;
        }
        if (strpos($relative, 'wp-content/') === 0) {
            if ($relative === 'wp-content/install.php') {
                prepRequire(prepJdmOwnedFile(new SplFileInfo($web . '/' . $relative), fileowner($web), 16165), 'Unexpected JDM wp-content/install.php metadata.');
                continue;
            }
            if ($relative === 'wp-content/object-cache.php') {
                prepRequire(prepJdmCacheDropIn(new SplFileInfo($web . '/' . $relative), $relative, fileowner($web)), 'Unrecognized JDM cache drop-in.');
                continue;
            }
            $contentTop = explode('/', substr($relative, 11))[0];
            prepRequire(in_array($contentTop, ['plugins', 'themes', 'uploads', 'mu-plugins', 'languages', 'index.php'], true), 'Unexpected wp-content content or drop-in.');
        }
    }
    foreach (['index.php', 'wp-config.php', 'wp-settings.php', 'wp-includes/version.php'] as $required) {
        prepRequire(is_file($web . '/' . $required), 'Expected preliminary WordPress files are missing.');
    }
    prepRequire(!file_exists($web . '/index.html') && !file_exists($web . '/deployment-status.json'), 'Static site already exists; preparation forbidden.');
}

function prepMove(string $home, int $uid): void {
    $web = $home . '/public_html';
    $holding = $home . '/.jdm-unused-installer-23048';
    prepDirectory($home, $uid);
    prepDirectory($web, $uid);
    prepRequire(!file_exists($holding) && !is_link($holding), 'Holding path already exists.');
    prepRequire(stat($web)['dev'] === stat($home)['dev'], 'Document root is on another filesystem; no fallback operation permitted.');
    $oldMode = fileperms($web) & 0777;
    prepRequire(rename($web, $holding), 'Cannot rename document root; no copy or deletion attempted.');
    if (!chmod($holding, 0700) || !mkdir($web, 0755)) {
        chmod($holding, $oldMode);
        prepRequire(rename($holding, $web), 'Preparation stopped; rollback needs manual review of this new site only.');
        throw new RuntimeException('Cannot create fresh document root; original directory restored.');
    }
    prepDirectory($web, $uid);
    prepRequire(chmod($web, 0755), 'Cannot set new document-root permissions.');
}

function prepMain(array $arguments): void {
    prepRequire(PHP_SAPI === 'cli' && extension_loaded('posix'), 'PHP CLI with posix is required.');
    prepRequire($arguments === [] || $arguments === ['--check'] || $arguments === ['--apply'], 'Only --check or --apply is accepted.');
    $apply = $arguments === ['--apply'];
    $uid = posix_geteuid();
    $account = posix_getpwuid($uid);
    $expected = posix_getpwnam(PREP_ACCOUNT);
    prepRequire(is_array($account) && is_array($expected) && $account['name'] === PREP_ACCOUNT && $uid === $expected['uid'] && $uid !== 0, 'Wrong system account; preparation forbidden.');
    $home = realpath($account['dir']);
    prepRequire(is_string($home) && $home === PREP_HOME && $home === $account['dir'] && !is_link($home), 'Unexpected account home.');
    prepRequire(getenv('HOME') === false || getenv('HOME') === '' || realpath(getenv('HOME')) === $home, 'Environment home/account mismatch.');
    prepDirectory($home, $uid);
    $web = $home . '/public_html';
    $holding = $home . '/.jdm-unused-installer-23048';
    $inventory = prepInventory($web, $uid);
    $state = $home . '/.sezam-nowa-deploy';
    if (!file_exists($state) && !is_link($state)) { prepRequire(mkdir($state, 0700), 'Cannot create private control directory.'); }
    prepDirectory($state, $uid);
    $lockPath = $state . '/deployment.lock';
    prepRequire(!is_link($lockPath) && (!file_exists($lockPath) || (is_file($lockPath) && fileowner($lockPath) === $uid)), 'Unsafe deployment lock.');
    $lock = fopen($lockPath, 'c');
    prepRequire($lock !== false && flock($lock, LOCK_EX | LOCK_NB), 'Another preparation/deployment is running.');
    try {
        if (file_exists($holding) || is_link($holding)) {
            prepInventory($holding, $uid);
            prepRequire((fileperms($holding) & 0777) === 0700, 'Existing holding directory is not private.');
            if ($inventory === []) { echo "Already prepared: empty document root.\n"; return; }
            $statusPath = $web . '/deployment-status.json';
            prepRequire(is_file($statusPath) && filesize($statusPath) < 16384, 'Existing preparation state requires manual review.');
            $status = json_decode(file_get_contents($statusPath), true);
            prepRequire(is_array($status) && ($status['site_id'] ?? null) === PREP_SITE_ID && ($status['origin'] ?? '') === PREP_ORIGIN && ($status['repository'] ?? '') === 'angsm111-dot/lombardgorzow' && is_file($web . '/index.html'), 'Document root is not the deployed SEZAM static site.');
            foreach ($inventory as $relative) { prepRequire(!preg_match('/(?:^|\/)wp-(?:admin|content|includes)(?:\/|$)|\.(?:php\d*|phtml|phar)(?:\.|$)/i', $relative), 'Unexpected PHP/WordPress content in prepared site.'); }
            echo "Already prepared: SEZAM static site is present.\n";
            return;
        }
        prepScaffold($web, $inventory);
        $fresh = prepInventory($web, $uid);
        sort($inventory); sort($fresh);
        prepRequire($fresh === $inventory, 'Scaffold inventory changed during checks.');
        prepScaffold($web, $fresh);
        if (!$apply) { echo "Checks passed: recognized new JDM scaffold for site 23048; --apply would rename it once and create an empty HTML root.\n"; return; }
        prepMove($home, $uid);
        echo "Prepared new site 23048: installer moved privately; empty HTML document root created. No copy, archive, database change or deletion.\n";
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}

try { prepMain(array_slice($argv, 1)); }
catch (Throwable $error) { fwrite(STDERR, 'Preparation stopped: ' . $error->getMessage() . "\n"); exit(1); }
