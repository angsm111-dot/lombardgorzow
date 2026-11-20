#!/usr/bin/env php
<?php
declare(strict_types=1);

/* One-time preparation of NEW JDM site 23048. Default: checks only. */
const PREP_ACCOUNT = 'vvictgzv';
const PREP_SITE_ID = 23048;
const PREP_ORIGIN = 'https://nowa.lombardgorzow.com';

function prepRequire(bool $ok, string $message): void {
    if (!$ok) { throw new RuntimeException($message); }
}

function prepDirectory(string $path, int $uid): void {
    prepRequire(!is_link($path) && is_dir($path) && fileowner($path) === $uid, 'Directory type or ownership mismatch.');
}

function prepInventory(string $directory, int $uid): array {
    prepDirectory($directory, $uid);
    $files = [];
    $iterator = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($directory, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::SELF_FIRST);
    foreach ($iterator as $item) {
        prepRequire(count($files) < 12000, 'Unexpectedly large scaffold.');
        prepRequire(!$item->isLink() && $item->getOwner() === $uid && ($item->isDir() || $item->isFile()), 'Unexpected path type, symbolic link or owner.');
        $files[] = substr($item->getPathname(), strlen($directory) + 1);
    }
    return $files;
}

function prepScaffold(string $web, array $inventory): void {
    $allowedRoot = ['wp-admin', 'wp-includes', 'wp-content', 'index.php', 'license.txt', 'readme.html', 'wp-activate.php', 'wp-blog-header.php', 'wp-comments-post.php', 'wp-config.php', 'wp-config-sample.php', 'wp-cron.php', 'wp-links-opml.php', 'wp-load.php', 'wp-login.php', 'wp-mail.php', 'wp-settings.php', 'wp-signup.php', 'wp-trackback.php', 'xmlrpc.php', '.htaccess'];
    foreach ($inventory as $relative) {
        $top = explode('/', $relative)[0];
        prepRequire(in_array($top, $allowedRoot, true), 'Unexpected content in the new document root.');
        prepRequire(strpos($relative, 'wp-content/uploads/') !== 0, 'Uploads directory is not empty.');
        prepRequire(strpos($relative, 'wp-content/mu-plugins/') !== 0, 'Must-use plugins require separate review.');
        if (strpos($relative, 'wp-content/') === 0) {
            $contentTop = explode('/', substr($relative, 11))[0];
            prepRequire(in_array($contentTop, ['plugins', 'themes', 'uploads', 'mu-plugins', 'languages', 'index.php'], true), 'Unexpected wp-content content or drop-in.');
        }
    }
    foreach (['index.php', 'wp-config.php', 'wp-settings.php', 'wp-includes/version.php'] as $required) {
        prepRequire(is_file($web . '/' . $required), 'Expected preliminary WordPress files are missing.');
    }
    prepRequire(!file_exists($web . '/index.html') && !file_exists($web . '/deployment-status.json'), 'Static site already exists; preparation forbidden.');
}

function prepWpBinary(): string {
    foreach (['/usr/local/bin/wp', '/usr/bin/wp'] as $candidate) {
        $resolved = realpath($candidate);
        if ($resolved !== false && is_file($resolved) && is_executable($resolved) && fileowner($resolved) === 0) { return $resolved; }
    }
    throw new RuntimeException('Trusted installed WP-CLI not found; no changes made.');
}

function prepCommand(array $command, string $cwd): array {
    /* Array invocation bypasses the shell; no command is built from user input. */
    $environment = ['PATH' => '/usr/local/bin:/usr/bin:/bin', 'WP_CLI_CONFIG_PATH' => '/dev/null', 'WP_CLI_DISABLE_AUTO_CHECK_UPDATE' => '1', 'WP_CLI_CACHE_DIR' => $cwd . '/wp-cli-cache'];
    $process = proc_open($command, [['pipe', 'r'], ['pipe', 'w'], ['pipe', 'w']], $pipes, $cwd, $environment);
    prepRequire(is_resource($process), 'Cannot start WP-CLI.');
    fclose($pipes[0]);
    stream_set_blocking($pipes[1], false);
    stream_set_blocking($pipes[2], false);
    $output = '';
    $errors = '';
    $deadline = microtime(true) + 90;
    $exit = -1;
    try {
        do {
            $output .= stream_get_contents($pipes[1]);
            $errors .= stream_get_contents($pipes[2]);
            prepRequire(strlen($output) + strlen($errors) <= 65536, 'WP-CLI output exceeded its limit.');
            $status = proc_get_status($process);
            if (!$status['running']) { $exit = $status['exitcode']; break; }
            prepRequire(microtime(true) < $deadline, 'WP-CLI check timed out.');
            usleep(50000);
        } while (true);
        $output .= stream_get_contents($pipes[1]);
        $errors .= stream_get_contents($pipes[2]);
    } finally {
        fclose($pipes[1]);
        fclose($pipes[2]);
        if (isset($status) && $status['running']) { proc_terminate($process); }
        $closed = proc_close($process);
    }
    if ($exit < 0) { $exit = $closed; }
    /* Raw command output is never displayed or logged; it can contain paths. */
    return ['exit' => $exit, 'output' => trim($output), 'errors' => trim($errors)];
}

function prepRequireUninstalled(array $result): void {
    prepRequire($result['exit'] === 1 && $result['output'] === '' && $result['errors'] === '', 'WP-CLI did not conclusively confirm an unconfigured installation.');
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
    prepRequire(PHP_SAPI === 'cli' && extension_loaded('posix') && function_exists('proc_open'), 'PHP CLI with posix and proc_open is required.');
    prepRequire($arguments === [] || $arguments === ['--check'] || $arguments === ['--apply'], 'Only --check or --apply is accepted.');
    $apply = $arguments === ['--apply'];
    $uid = posix_geteuid();
    $account = posix_getpwuid($uid);
    $expected = posix_getpwnam(PREP_ACCOUNT);
    prepRequire(is_array($account) && is_array($expected) && $account['name'] === PREP_ACCOUNT && $uid === $expected['uid'] && $uid !== 0, 'Wrong system account; preparation forbidden.');
    $home = realpath($account['dir']);
    prepRequire(is_string($home) && $home === $account['dir'] && !is_link($home), 'Unexpected account home.');
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
        /* Prevent project/global YAML and environment hooks from changing fixed commands. */
        for ($directory = $state; ; $directory = dirname($directory)) {
            prepRequire(!file_exists($directory . '/wp-cli.yml') && !file_exists($directory . '/wp-cli.local.yml'), 'WP-CLI project configuration requires separate review.');
            if ($directory === dirname($directory)) { break; }
        }
        $wp = prepWpBinary();
        $flags = ['--path=' . $web, '--skip-plugins', '--skip-themes', '--skip-packages', '--no-color'];
        $version = prepCommand(array_merge([$wp, '--version'], $flags), $state);
        prepRequire($version['exit'] === 0 && preg_match('/^WP-CLI [0-9]+\.[0-9]+(?:\.[0-9]+)?(?:[-.A-Za-z0-9]*)$/D', $version['output']) === 1 && $version['errors'] === '', 'Installed WP-CLI could not be confirmed.');
        $checksums = prepCommand(array_merge([$wp, 'core', 'verify-checksums', '--quiet'], $flags), $state);
        prepRequire($checksums['exit'] === 0 && $checksums['errors'] === '', 'Official WordPress core checksums did not pass; no changes made.');
        prepRequireUninstalled(prepCommand(array_merge([$wp, 'core', 'is-installed'], $flags), $state));
        $fresh = prepInventory($web, $uid);
        sort($inventory); sort($fresh);
        prepRequire($fresh === $inventory, 'Scaffold inventory changed during checks.');
        prepScaffold($web, $fresh);
        if (!$apply) { echo "Checks passed: new unconfigured scaffold; --apply would rename it once and create an empty HTML root.\n"; return; }
        prepMove($home, $uid);
        echo "Prepared new site 23048: installer moved privately; empty HTML document root created. No copy, archive, database change or deletion.\n";
    } finally {
        flock($lock, LOCK_UN);
        fclose($lock);
    }
}

try { prepMain(array_slice($argv, 1)); }
catch (Throwable $error) { fwrite(STDERR, 'Preparation stopped: ' . $error->getMessage() . "\n"); exit(1); }
