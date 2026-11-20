#!/usr/bin/env bash
# One-site archive migration. Default is read-only. See docs/archive-wordpress-jdm.md.
set -Eeuo pipefail
umask 077
export LC_ALL=C

MODE="${1:---check}"
[[ $# -le 1 && ( "$MODE" == --check || "$MODE" == --apply ) ]] || {
  printf 'Usage: bash archive-wordpress-jdm.sh [--check|--apply]\n' >&2
  exit 2
}
readonly ACCOUNT='lombard1'
readonly DOCROOT='/home/lombard1/public_html'
readonly CONTENT="$DOCROOT/wp-content"
readonly ARCHIVE='https://stara.lombardgorzow.com'
readonly PRODUCTION='https://lombardgorzow.com'
readonly STATE_DIR='/home/lombard1/sezam-wp-archive-state'
readonly STATE="$STATE_DIR/original-settings.json"
readonly PLUGIN="$CONTENT/mu-plugins/sezam-old-site.php"
# Matches all four HTTP(S), www/non-www origins, including JSON-escaped slashes.
# The hostname boundary prevents matching lombardgorzow.com.example or .com.pl.
readonly OLD_PATTERN='https?:\\?/\\?/(?:www\.)?lombardgorzow\.com(?![A-Za-z0-9.-])'
STAGE='environment-check'
fail() { printf 'STOP: %s\n' "$1" >&2; exit 1; }
trap 'printf "STOP: stage=%s. No raw WP/SQL errors are printed. Review the private state and documentation before continuing.\n" "$STAGE" >&2' ERR

for executable in id hostname readlink stat php wp sed; do
  command -v "$executable" >/dev/null 2>&1 || fail "Required executable unavailable: $executable"
done
[[ "$(id -un)" == "$ACCOUNT" ]] || fail 'Run as account lombard1; do not run as root or another hosting account.'
[[ "$(hostname -s)" == web16 ]] || fail 'Expected JDM host web16.'
[[ -d "$DOCROOT" && "$(readlink -f "$DOCROOT")" == "$DOCROOT" ]] || fail 'Document root is absent, moved or symlinked.'
[[ "$(stat -c '%U' "$DOCROOT")" == "$ACCOUNT" ]] || fail 'Unexpected document-root owner.'
for path in "$DOCROOT/wp-config.php" "$DOCROOT/wp-settings.php" "$DOCROOT/wp-load.php"; do
  [[ -f "$path" && ! -L "$path" && "$(stat -c '%U' "$path")" == "$ACCOUNT" ]] || fail 'Unexpected WordPress files, symlinks or owners.'
done
[[ -d "$CONTENT" && ! -L "$CONTENT" && "$(readlink -f "$CONTENT")" == "$CONTENT" ]] || fail 'Unexpected wp-content path.'
[[ "$(stat -c '%U' "$CONTENT")" == "$ACCOUNT" ]] || fail 'Unexpected wp-content owner.'
if [[ -e "$CONTENT/mu-plugins" ]]; then
  [[ -d "$CONTENT/mu-plugins" && ! -L "$CONTENT/mu-plugins" && "$(stat -c '%U' "$CONTENT/mu-plugins")" == "$ACCOUNT" ]] || fail 'Unexpected mu-plugins path or owner.'
fi
if [[ -e "$STATE_DIR" ]]; then
  [[ -d "$STATE_DIR" && ! -L "$STATE_DIR" && "$(stat -c '%U' "$STATE_DIR")" == "$ACCOUNT" ]] || fail 'Unexpected private state directory.'
fi
# WP_CLI_CONFIG_PATH suppresses only the global file. Project/ancestor YAML can
# contain require/ssh/http settings, so block it before the first WP-CLI process.
config_dir="$DOCROOT"
while :; do
  for config_name in wp-cli.yml wp-cli.local.yml; do
    [[ ! -e "$config_dir/$config_name" && ! -L "$config_dir/$config_name" ]] || fail 'Project/ancestor WP-CLI YAML exists; review it explicitly before using this bounded helper.'
  done
  [[ "$config_dir" != / ]] || break
  config_dir="${config_dir%/*}"
  [[ -n "$config_dir" ]] || config_dir=/
done
cd "$DOCROOT"
# Avoid package hooks and regular plugins/themes; must-use plugins and drop-ins can
# still load, as documented by WP-CLI. We do not alter their files or configuration.
export WP_CLI_CONFIG_PATH=/dev/null
WP=(wp --path="$DOCROOT" --url="$ARCHIVE" --skip-plugins --skip-themes --skip-packages --no-color --quiet)
WP+=(--exec='if (!defined("DISABLE_WP_CRON")) { define("DISABLE_WP_CRON", true); } WP_CLI::add_hook("after_wp_config_load", function () { $GLOBALS["sezam_archive_precore_constants"] = array(); foreach (array("WP_CONTENT_URL", "WP_PLUGIN_URL", "UPLOADS") as $name) { if (defined($name)) { $GLOBALS["sezam_archive_precore_constants"][] = $name; } } });')
wp_version="$(wp --skip-packages --version 2>/dev/null)" || fail 'WP-CLI could not start.'
[[ "$wp_version" =~ ^WP-CLI\ [0-9A-Za-z.+_-]+$ ]] || fail 'Unexpected WP-CLI version output; not printed.'
printf 'wp_cli_installed=true\nwp_cli=%s\naccount=lombard1\nhost=web16\npath=%s\n' "$wp_version" "$DOCROOT"

AUDIT_PHP=$(cat <<'PHP'
global $wpdb, $wp_version, $sezam_archive_precore_constants;
$wpdb->suppress_errors(true);
$allowed = array('http://lombardgorzow.com', 'https://lombardgorzow.com', 'http://www.lombardgorzow.com', 'https://www.lombardgorzow.com', 'https://stara.lombardgorzow.com');
$errors = array();
if (!isset($sezam_archive_precore_constants) || !is_array($sezam_archive_precore_constants)) {
    WP_CLI::error('Configuration hook did not run; cannot distinguish overrides from defaults.');
}
foreach ($sezam_archive_precore_constants as $override) {
    $errors[] = $override . ' is defined by configuration; review it explicitly before migration.';
}
$prefix = (string) $wpdb->prefix;
if (!preg_match('/^[A-Za-z0-9_]+$/D', $prefix)) { WP_CLI::error('Unexpected table prefix.'); }
$tables = $wpdb->get_col($wpdb->prepare('SHOW TABLES LIKE %s', $wpdb->esc_like($prefix) . '%'));
if (!$tables) { WP_CLI::error('No matching tables.'); }
sort($tables);
$other_options = 0; $missing_primary_key = 0;
foreach ($tables as $table) {
    if (!preg_match('/^[A-Za-z0-9_]+$/D', $table)) { WP_CLI::error('Unexpected table identifier.'); }
    if (substr($table, -7) === 'options' && $table !== $wpdb->options) { $other_options++; }
    $primary = $wpdb->get_results("SHOW KEYS FROM `" . $table . "` WHERE Key_name = 'PRIMARY'");
    if (!$primary) { $missing_primary_key++; }
}
if ($other_options) { $errors[] = 'Other options tables share the prefix; review site boundaries.'; }
if ($missing_primary_key) { $errors[] = 'Some prefixed tables lack a primary key; WP-CLI would skip them.'; }
if (is_multisite() || $wpdb->base_prefix !== $prefix) { $errors[] = 'Multisite is not supported.'; }
if (defined('CUSTOM_USER_TABLE') || defined('CUSTOM_USER_META_TABLE')) { $errors[] = 'Shared custom user tables require manual review.'; }
if (defined('RELOCATE') && RELOCATE) { $errors[] = 'RELOCATE must be reviewed before migration.'; }
$raw = array();
foreach (array('home', 'siteurl', 'blog_public') as $option) {
    $raw[$option] = $wpdb->get_var($wpdb->prepare("SELECT option_value FROM `" . $wpdb->options . "` WHERE option_name = %s", $option));
}
$safe_url = function ($value) use ($allowed) {
    return is_string($value) && in_array(rtrim($value, '/'), $allowed, true) ? $value : '[unexpected URL]';
};
foreach (array('home', 'siteurl') as $option) {
    if ($safe_url($raw[$option]) === '[unexpected URL]') { $errors[] = 'Unexpected database ' . $option . '.'; }
}
$constants = array();
foreach (array('WP_HOME', 'WP_SITEURL') as $name) {
    $constants[$name] = array('defined' => defined($name), 'value' => defined($name) ? $safe_url(constant($name)) : null);
    if (defined($name)) { $errors[] = $name . ' is defined; review/remove the override explicitly before applying.'; }
}
if (defined('COOKIE_DOMAIN') && COOKIE_DOMAIN) { $errors[] = 'COOKIE_DOMAIN override requires manual review.'; }
$expected_content = '/home/lombard1/public_html/wp-content';
if (rtrim(WP_CONTENT_DIR, '/') !== $expected_content) { $errors[] = 'Custom WP_CONTENT_DIR is not supported.'; }
if (rtrim(WPMU_PLUGIN_DIR, '/') !== $expected_content . '/mu-plugins') { $errors[] = 'Custom WPMU_PLUGIN_DIR is not supported.'; }
if (defined('WP_CONTENT_URL') && rtrim(WP_CONTENT_URL, '/') !== untrailingslashit(site_url()) . '/wp-content') {
    $errors[] = 'Unexpected WP_CONTENT_URL; review its source before migration.';
}
$counts = array();
foreach (array('post', 'page', 'attachment') as $type) {
    $status = $type === 'attachment' ? 'inherit' : 'publish';
    $counts[$type] = (int) $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM `" . $wpdb->posts . "` WHERE post_type = %s AND post_status = %s", $type, $status));
}
if ($counts['post'] < 1 || $counts['page'] < 1) { $errors[] = 'Published content is missing.'; }
if (!in_array((string) $raw['blog_public'], array('0', '1'), true)) { $errors[] = 'Unexpected blog_public value.'; }
$effective_home = untrailingslashit(home_url());
$effective_siteurl = untrailingslashit(site_url());
if ($safe_url($effective_home) === '[unexpected URL]' || $safe_url($effective_siteurl) === '[unexpected URL]') { $errors[] = 'Unexpected effective WordPress URL.'; }
$report = array(
    'wordpress_version' => preg_match('/^[0-9A-Za-z.+_-]+$/D', $wp_version) ? $wp_version : '[unexpected version]',
    'home' => $safe_url($raw['home']), 'siteurl' => $safe_url($raw['siteurl']),
    'effective_home' => $safe_url($effective_home), 'effective_siteurl' => $safe_url($effective_siteurl),
    'blog_public' => in_array((string) $raw['blog_public'], array('0','1'), true) ? (string) $raw['blog_public'] : '[unexpected]',
    'url_constants' => $constants, 'configured_content_overrides' => $sezam_archive_precore_constants, 'multisite' => is_multisite(),
    'table_prefix' => $prefix, 'prefixed_tables' => count($tables),
    'tables_without_primary_key' => $missing_primary_key, 'other_options_tables' => $other_options,
    'content_counts' => $counts,
    'empty_published_posts' => (int) $wpdb->get_var("SELECT COUNT(*) FROM `" . $wpdb->posts . "` WHERE post_type = 'post' AND post_status = 'publish' AND TRIM(post_content) = ''"),
    'table_set_sha256' => hash('sha256', implode("\n", $tables)),
    'database_identity_sha256' => hash('sha256', DB_HOST . "\n" . DB_NAME . "\n" . $prefix),
    'blockers' => $errors
);
if ($wpdb->last_error) { WP_CLI::error('Database audit failed.'); }
WP_CLI::line('JDM_ARCHIVE_REPORT:' . json_encode($report, JSON_UNESCAPED_SLASHES));
PHP
)

audit() {
  local raw result
  raw="$("${WP[@]}" eval "$AUDIT_PHP" 2>/dev/null)" || fail 'WordPress read-only audit failed; raw output withheld.'
  result="$(printf '%s\n' "$raw" | sed -n 's/^JDM_ARCHIVE_REPORT://p')"
  printf '%s' "$result" | php -r '$r=json_decode(stream_get_contents(STDIN),true); if (!is_array($r) || !isset($r["blockers"],$r["content_counts"])) { exit(1); } echo json_encode($r,JSON_UNESCAPED_SLASHES);' 2>/dev/null || fail 'Invalid sanitized audit result.'
}
report="$(audit)"
# Public-safe report excludes even non-secret database identity/table fingerprints.
printf '%s' "$report" | php -r '$r=json_decode(stream_get_contents(STDIN),true); unset($r["database_identity_sha256"],$r["table_set_sha256"]); echo json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES),"\n";'
blockers="$(printf '%s' "$report" | php -r '$r=json_decode(stream_get_contents(STDIN),true); echo count($r["blockers"]);')"
[[ "$blockers" == 0 ]] || fail 'Preflight blockers are listed above; no changes made.'

SR_ARGS=(--all-tables-with-prefix --skip-columns=guid --precise --recurse-objects --regex --regex-delimiter='~' --regex-flags=i --format=count)
search_count() {
  local pattern="$1" replacement="$2" value
  shift 2
  value="$("${WP[@]}" search-replace "$pattern" "$replacement" "${SR_ARGS[@]}" "$@" 2>/dev/null)" || fail 'Search-replace failed; raw output withheld.'
  [[ "$value" =~ ^[0-9]+$ ]] || fail 'Unexpected search-replace output; withheld.'
  printf '%s' "$value"
}
STAGE='read-only-dry-run'
old_count="$(search_count "$OLD_PATTERN" "$ARCHIVE" --dry-run)"
archive_count="$(search_count 'https?:\\?/\\?/stara\.lombardgorzow\.com(?![A-Za-z0-9.-])' 'https://archive-check.invalid' --dry-run)"
printf 'old_origin_replacements_dry_run=%s\nexisting_archive_references=%s\n' "$old_count" "$archive_count"
if [[ -f "$STATE" ]]; then printf 'private_migration_state=present\n'; else printf 'private_migration_state=absent\n'; fi
if [[ -f "$PLUGIN" ]]; then printf 'archive_mu_plugin=present\n'; else printf 'archive_mu_plugin=absent\n'; fi
if [[ "$MODE" == --check ]]; then
  printf 'mode=check\nresult=read_only_complete\n'
  exit 0
fi

STAGE='apply-preflight'
command -v curl >/dev/null 2>&1 || fail 'curl is required to verify the completed production cutover.'
command -v flock >/dev/null 2>&1 || fail 'flock is required for one-site migration locking.'
[[ ! -e "$STATE" && ! -e "$PLUGIN" && ! -L "$PLUGIN" ]] || fail 'Existing migration state/plugin: inspect --check and rollback instructions; automatic re-application is disabled.'
[[ "$archive_count" == 0 ]] || fail 'Archive URLs already exist in the database; review them before a reversible first migration.'
printf '%s' "$report" | php -r '$r=json_decode(stream_get_contents(STDIN),true); foreach(array("home","siteurl") as $k){if(rtrim($r[$k],"/")==="https://stara.lombardgorzow.com"){exit(1);}}' || fail 'WordPress is already using the archive origin.'
[[ -w "$CONTENT" && -w "$DOCROOT" ]] || fail 'WordPress content directory is not writable by lombard1.'
# Hard post-cutover gate: no WordPress URL changes while the old homepage is live.
production_html="$(curl --fail --silent --proto '=https' --max-redirs 0 --connect-timeout 5 --max-time 20 "$PRODUCTION/")" || fail 'Cannot verify the new HTTPS production homepage.'
[[ "$production_html" == *'page-home-calculator'* && "$production_html" == *'https://lombardgorzow.com/'* && "$production_html" != *'/wp-content/'* ]] || fail 'Production does not yet look like the new calculator homepage; no changes made.'
unset production_html
archive_status="$(curl --silent --proto '=https' --head --output /dev/null --write-out '%{http_code}' --max-redirs 0 --connect-timeout 5 --max-time 20 "$ARCHIVE/")" || fail 'Archive HTTPS alias is not reachable.'
[[ "$archive_status" =~ ^(200|301|302|307|308)$ ]] || fail 'Archive alias returned an unexpected status.'
# A 200/301 alone is not enough: the archive alias must expose a known record
# from this exact legacy WordPress, without following a redirect to another host.
archive_identity="$(curl --fail --silent --proto '=https' --max-redirs 0 --connect-timeout 5 --max-time 20 "$ARCHIVE/wp-json/wp/v2/posts/14219?_fields=id,slug")" || fail 'Cannot verify the old WordPress REST record through the archive alias.'
printf '%s' "$archive_identity" | php -r '$r=json_decode(stream_get_contents(STDIN),true); if(!is_array($r) || ($r["id"] ?? null)!==14219 || ($r["slug"] ?? null)!=="lombard-w-gorzowie-telefony-i-laptopy-pod-zastaw"){exit(1);}' || fail 'The archive alias has not been verified as this old WordPress; no changes made.'
unset archive_identity

# This is small rollback metadata, not a WordPress copy or database export.
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
exec 9>"$STATE_DIR/migration.lock"
flock -n 9 || fail 'Another migration is running.'
[[ ! -e "$STATE" && ! -e "$PLUGIN" ]] || fail 'Migration state appeared while waiting for the lock.'
latest="$(audit)"
[[ "$latest" == "$report" ]] || fail 'WordPress state changed since preflight; rerun --check.'

STAGE='prepare-mu-plugin'
plugin_tmp="$(mktemp "$STATE_DIR/sezam-old-site.XXXXXX.php")"
cat > "$plugin_tmp" <<'PHP'
<?php
/**
 * Plugin Name: SEZAM old website notice
 * Description: Noindex and a visible link to the current site, only on the archive hostname.
 * Version: 1.0.0
 */
if (!defined('ABSPATH') || (defined('WP_CLI') && WP_CLI)) { return; }
function sezam_old_site_is_archive() {
    $host = isset($_SERVER['HTTP_HOST']) ? strtolower(preg_replace('/:[0-9]+$/', '', $_SERVER['HTTP_HOST'])) : '';
    return $host === 'stara.lombardgorzow.com';
}
if (!sezam_old_site_is_archive()) { return; }
if (!headers_sent()) { header('X-Robots-Tag: noindex, follow', true); }
add_action('send_headers', function () {
    if (!headers_sent()) { header('X-Robots-Tag: noindex, follow', true); }
});
add_filter('wp_robots', function ($robots) {
    unset($robots['index'], $robots['nofollow']);
    $robots['noindex'] = true;
    $robots['follow'] = true;
    return $robots;
}, 999);
add_filter('wp_sitemaps_enabled', '__return_false');
// Let crawlers read the noindex response; do not advertise archive sitemaps.
add_filter('robots_txt', function () { return "User-agent: *\nDisallow:\n"; }, 999);
function sezam_old_site_banner() {
    static $shown = false;
    if ($shown || is_admin()) { return; }
    $shown = true;
    echo '<aside role="note" aria-label="Archiwalna strona" style="position:fixed;bottom:0;left:0;right:0;z-index:2147483000;padding:12px 18px;background:#3e302c;color:#fff;font:16px/1.5 sans-serif;text-align:center;box-shadow:0 -2px 10px #0003">To jest stara, archiwalna wersja strony. <a href="https://lombardgorzow.com/" style="color:#ffe0a3;text-decoration:underline;font-weight:bold">Przejdź do aktualnej strony Lombard SEZAM</a>.</aside>';
}
add_action('wp_body_open', 'sezam_old_site_banner', 1);
add_action('wp_footer', 'sezam_old_site_banner', 999);
PHP
php -l "$plugin_tmp" >/dev/null 2>&1 || fail 'Archive plugin PHP lint failed; database unchanged.'
state_tmp="$(mktemp "$STATE_DIR/original-settings.XXXXXX.json")"
printf '%s' "$report" | php -r '$r=json_decode(stream_get_contents(STDIN),true); $r["state_version"]=1; $r["status"]="prepared"; $r["prepared_at_utc"]=gmdate("c"); $r["archive_origin"]="https://stara.lombardgorzow.com"; $r["mu_plugin_preexisting"]=false; echo json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES),"\n";' > "$state_tmp"
chmod 600 "$state_tmp"
mv -n "$state_tmp" "$STATE"
[[ -f "$STATE" ]] || fail 'Could not preserve original settings.'
mkdir -p "$CONTENT/mu-plugins"
chmod 755 "$CONTENT/mu-plugins"
chmod 644 "$plugin_tmp"
mv -n "$plugin_tmp" "$PLUGIN"
[[ -f "$PLUGIN" ]] || fail 'Could not install archive-only plugin.'

STAGE='database-origin-replacement'
changed="$(search_count "$OLD_PATTERN" "$ARCHIVE")"
printf 'changed_fields=%s\n' "$changed"
STAGE='archive-options'
# Explicit update_option calls also invalidate these specific options in cache.
"${WP[@]}" option update home "$ARCHIVE" >/dev/null 2>&1 || fail 'Could not update home; see rollback metadata.'
"${WP[@]}" option update siteurl "$ARCHIVE" >/dev/null 2>&1 || fail 'Could not update siteurl; see rollback metadata.'
"${WP[@]}" option update blog_public 0 >/dev/null 2>&1 || fail 'Could not disable indexing; see rollback metadata.'
# Invalidate only this site's post/option entries, never a shared global cache.
"${WP[@]}" eval 'global $wpdb; foreach ($wpdb->get_col("SELECT ID FROM `".$wpdb->posts."`") as $id) { clean_post_cache((int)$id); } foreach ($wpdb->get_col("SELECT option_name FROM `".$wpdb->options."`") as $key) { wp_cache_delete($key, "options"); } wp_cache_delete("alloptions", "options"); wp_cache_delete("notoptions", "options");' >/dev/null 2>&1 || fail 'Scoped cache invalidation failed; inspect the archive before retrying.'
STAGE='postflight'
after="$(audit)"
printf '%s\n%s' "$report" "$after" | php -r '$lines=explode("\n",stream_get_contents(STDIN));$before=json_decode($lines[0],true);$after=json_decode($lines[1],true);if($after["home"]!=="https://stara.lombardgorzow.com" || $after["siteurl"]!=="https://stara.lombardgorzow.com" || $after["blog_public"]!=="0" || $after["blockers"] || $after["content_counts"]!==$before["content_counts"] || $after["database_identity_sha256"]!==$before["database_identity_sha256"] || $after["table_set_sha256"]!==$before["table_set_sha256"]){exit(1);}' || fail 'Postflight mismatch; review private state before any further changes.'
remaining="$(search_count "$OLD_PATTERN" "$ARCHIVE" --dry-run)"
[[ "$remaining" == 0 ]] || fail 'Old origin references remain outside GUID; inspect before retrying.'
php -r '$p=$argv[1];$r=json_decode(file_get_contents($p),true);$r["status"]="applied";$r["applied_at_utc"]=gmdate("c");$tmp=$p.".completed";if(file_put_contents($tmp,json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)."\n")===false){exit(1);}chmod($tmp,0600);if(!rename($tmp,$p)){exit(1);}' "$STATE"
printf 'mode=apply\nresult=archive_configured\narchive=%s\noriginal_settings=%s\n' "$ARCHIVE" "$STATE"
printf 'Next: verify archive HTML, assets, login, redirects and X-Robots-Tag over HTTPS; purge only this site’s page/hosting cache if necessary.\n'
