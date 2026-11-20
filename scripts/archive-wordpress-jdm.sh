#!/usr/bin/env bash
# One-site archive migration. Default does not change WordPress files or data. See docs/archive-wordpress-jdm.md.
set -Eeuo pipefail
umask 077
export LC_ALL=C

MODE="${1:---check}"
[[ $# -le 1 && ( "$MODE" == --check || "$MODE" == --apply || "$MODE" == --diagnose || "$MODE" == --diagnose-table ) ]] || {
  printf 'Usage: bash archive-wordpress-jdm.sh [--check|--diagnose|--diagnose-table|--apply]\n' >&2
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

for executable in id hostname readlink stat php wp sed mktemp mkdir chmod cat; do
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
if [[ -e "$STATE_DIR" || -L "$STATE_DIR" ]]; then
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
STAGE='private-runtime-files'
# JDM's PHP wrapper splits arguments containing spaces. Execute PHP from private
# files instead of passing source code in argv, including WP-CLI startup hooks.
mkdir -p "$STATE_DIR"
chmod 700 "$STATE_DIR"
[[ -d "$STATE_DIR" && ! -L "$STATE_DIR" && "$(readlink -f "$STATE_DIR")" == "$STATE_DIR" && "$(stat -c '%U' "$STATE_DIR")" == "$ACCOUNT" ]] || fail 'Unexpected private state directory after creation.'
runtime_dir="$(mktemp -d "$STATE_DIR/runtime.XXXXXXXX")"
[[ -d "$runtime_dir" && ! -L "$runtime_dir" && "$(stat -c '%U' "$runtime_dir")" == "$ACCOUNT" ]] || fail 'Unexpected private runtime directory.'
chmod 700 "$runtime_dir"
# Each destination is new under this unique owner-only directory; noclobber
# prevents accidental overwrites. These are helper files, not WordPress files.
write_php() {
  local name="$1"
  [[ "$name" =~ ^[a-z][a-z0-9-]*\.php$ ]] || fail 'Unexpected private PHP filename.'
  (set -o noclobber; { printf '<?php\n'; cat; } > "$runtime_dir/$name") || fail 'Could not create private PHP helper.'
  chmod 600 "$runtime_dir/$name"
}
write_php bootstrap.php <<'PHP'
if (!defined("DISABLE_WP_CRON")) { define("DISABLE_WP_CRON", true); } WP_CLI::add_hook("after_wp_config_load", function () { $GLOBALS["sezam_archive_precore_constants"] = array(); foreach (array("WP_CONTENT_URL", "WP_PLUGIN_URL", "UPLOADS") as $name) { if (defined($name)) { $GLOBALS["sezam_archive_precore_constants"][] = $name; } } });
PHP

cd "$DOCROOT"
# Avoid package hooks and regular plugins/themes; must-use plugins and drop-ins can
# still load, as documented by WP-CLI. We do not alter their files or configuration.
export WP_CLI_CONFIG_PATH=/dev/null
WP=(wp --path="$DOCROOT" --url="$ARCHIVE" --skip-plugins --skip-themes --skip-packages --no-color --quiet)
WP+=(--require="$runtime_dir/bootstrap.php")
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

printf '%s\n' "$AUDIT_PHP" | write_php audit.php
write_php normalize-report.php <<'PHP'
$r=json_decode(stream_get_contents(STDIN),true); if (!is_array($r) || !isset($r["blockers"],$r["content_counts"])) { exit(1); } echo json_encode($r,JSON_UNESCAPED_SLASHES);
PHP
write_php public-report.php <<'PHP'
$r=json_decode(stream_get_contents(STDIN),true); unset($r["database_identity_sha256"],$r["table_set_sha256"]); echo json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES),"\n";
PHP
write_php count-blockers.php <<'PHP'
$r=json_decode(stream_get_contents(STDIN),true); echo count($r["blockers"]);
PHP
write_php reject-existing-archive.php <<'PHP'
$r=json_decode(stream_get_contents(STDIN),true); foreach(array("home","siteurl") as $k){if(rtrim($r[$k],"/")==="https://stara.lombardgorzow.com"){exit(1);}}
PHP
write_php verify-archive-identity.php <<'PHP'
$r=json_decode(stream_get_contents(STDIN),true); if(!is_array($r) || ($r["id"] ?? null)!==14219 || ($r["slug"] ?? null)!=="lombard-w-gorzowie-telefony-i-laptopy-pod-zastaw"){exit(1);}
PHP
write_php prepare-state.php <<'PHP'
$r=json_decode(stream_get_contents(STDIN),true); $r["state_version"]=1; $r["status"]="prepared"; $r["prepared_at_utc"]=gmdate("c"); $r["archive_origin"]="https://stara.lombardgorzow.com"; $r["mu_plugin_preexisting"]=false; echo json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES),"\n";
PHP
write_php verify-postflight.php <<'PHP'
$lines=explode("\n",stream_get_contents(STDIN));$before=json_decode($lines[0],true);$after=json_decode($lines[1],true);if($after["home"]!=="https://stara.lombardgorzow.com" || $after["siteurl"]!=="https://stara.lombardgorzow.com" || $after["blog_public"]!=="0" || $after["blockers"] || $after["content_counts"]!==$before["content_counts"] || $after["database_identity_sha256"]!==$before["database_identity_sha256"] || $after["table_set_sha256"]!==$before["table_set_sha256"]){exit(1);}
PHP
write_php complete-state.php <<'PHP'
$p=$argv[1];$r=json_decode(file_get_contents($p),true);$r["status"]="applied";$r["applied_at_utc"]=gmdate("c");$tmp=$p.".completed";if(file_put_contents($tmp,json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES)."\n")===false){exit(1);}chmod($tmp,0600);if(!rename($tmp,$p)){exit(1);}
PHP
write_php invalidate-cache.php <<'PHP'
global $wpdb; foreach ($wpdb->get_col("SELECT ID FROM `".$wpdb->posts."`") as $id) { clean_post_cache((int)$id); } foreach ($wpdb->get_col("SELECT option_name FROM `".$wpdb->options."`") as $key) { wp_cache_delete($key, "options"); } wp_cache_delete("alloptions", "options"); wp_cache_delete("notoptions", "options");
PHP
write_php diagnostic-eval-without-wordpress.php <<'PHP'
WP_CLI::line("JDM_DIAG_NO_WP:" . json_encode(array("php_version" => PHP_VERSION, "mysqli_available" => extension_loaded("mysqli"))));
PHP
write_php diagnostic-wordpress-bootstrap.php <<'PHP'
global $sezam_archive_precore_constants; WP_CLI::line("JDM_DIAG_BOOTSTRAP:" . json_encode(array("config_hook_present" => isset($sezam_archive_precore_constants) && is_array($sezam_archive_precore_constants), "php_version" => PHP_VERSION, "mysqli_available" => extension_loaded("mysqli"))));
PHP

write_php table-diagnostic-guard.php <<'PHP'
$r=json_decode(stream_get_contents(STDIN),true);
$allowed=array('http://lombardgorzow.com','https://lombardgorzow.com','http://www.lombardgorzow.com','https://www.lombardgorzow.com');
if(!is_array($r) || $r['table_prefix']!=='wp_' || $r['tables_without_primary_key']!==1 || $r['blockers']!==array('Some prefixed tables lack a primary key; WP-CLI would skip them.') || !in_array(rtrim($r['home'],'/'),$allowed,true) || !in_array(rtrim($r['siteurl'],'/'),$allowed,true)){exit(1);}
PHP
write_php diagnose-table.php <<'PHP'
global $wpdb;
$wpdb->suppress_errors(true);
if ($wpdb->prefix !== 'wp_' || $wpdb->base_prefix !== 'wp_' || is_multisite()) { WP_CLI::error('Unexpected table diagnostic boundary.'); }
$tables=$wpdb->get_col($wpdb->prepare('SHOW TABLES LIKE %s',$wpdb->esc_like('wp_').'%'));
$missing=array();
foreach($tables as $table){
    if(!preg_match('/^wp_[A-Za-z0-9_]+$/D',$table)){WP_CLI::error('Unexpected table identifier.');}
    $keys=$wpdb->get_results("SHOW KEYS FROM `".$table."` WHERE Key_name = 'PRIMARY'");
    if($wpdb->last_error){WP_CLI::error('Table key query failed.');}
    if(!$keys){$missing[]=$table;}
}
if(count($missing)!==1){WP_CLI::error('Expected exactly one table without a primary key.');}
$table=$missing[0];
$structure=$wpdb->get_results('SHOW FULL COLUMNS FROM `'.$table.'`',ARRAY_A);
if($wpdb->last_error || !$structure || count($structure)>32){WP_CLI::error('Column metadata exceeds diagnostic bounds.');}
$columns=array();$lengths=array();$projection=array();
foreach($structure as $column){
    $name=$column['Field'];
    if(!preg_match('/^[A-Za-z0-9_]+$/D',$name) || !preg_match('/^([A-Za-z]+)/',$column['Type'],$type)){WP_CLI::error('Unexpected column metadata.');}
    // Only the base type is exposed: enum/set definitions and defaults can hold values.
    $columns[]=array('name'=>$name,'type'=>strtolower($type[1]),'nullable'=>$column['Null']==='YES','unique_key'=>$column['Key']==='UNI','auto_increment'=>strpos($column['Extra'],'auto_increment')!==false,'old_origin_occurrences'=>0,'matching_cells'=>0);
    $lengths[]='COALESCE(OCTET_LENGTH(CAST(`'.$name.'` AS BINARY)),0)';
    $projection[]='LEFT(CAST(`'.$name.'` AS BINARY),65537) AS `'.$name.'`';
}
$summary_sql='SELECT COUNT(*) AS row_count, COALESCE(SUM('.implode('+',$lengths).'),0) AS byte_count FROM `'.$table.'`';
$before=$wpdb->get_row($summary_sql,ARRAY_A);
if($wpdb->last_error || !is_array($before)){WP_CLI::error('Table size query failed.');}
$row_count=(int)$before['row_count'];$bytes=(int)$before['byte_count'];
$result=array('table'=>$table,'has_primary_key'=>false,'row_count'=>$row_count,'columns'=>$columns,'scan_complete'=>false,'limit_reason'=>null,'scanned_rows'=>0,'scanned_bytes'=>0,'old_origin_occurrences'=>0,'matching_rows'=>0,'matching_cells'=>0);
if($row_count>5000 || $bytes>8388608){
    $result['limit_reason']='table_size_limit';
}else{
    $pattern=<<<'REGEX'
~https?:\\?/\\?/(?:www\.)?lombardgorzow\.com(?![A-Za-z0-9.-])~i
REGEX;
    for($offset=0;$offset<$row_count;$offset+=16){
        $rows=$wpdb->get_results('SELECT '.implode(',',$projection).' FROM `'.$table.'` LIMIT 16 OFFSET '.(int)$offset,ARRAY_A);
        if($wpdb->last_error || !is_array($rows)){WP_CLI::error('Bounded table scan failed.');}
        foreach($rows as $row){
            $row_matches=false;
            foreach($result['columns'] as $index=>$column){
                $value=$row[$column['name']];
                if($value===null){continue;}
                $length=strlen($value);
                if($length>65536 || $result['scanned_bytes']+$length>8388608){$result['limit_reason']='cell_or_byte_limit';break 3;}
                $result['scanned_bytes']+=$length;
                $matches=preg_match_all($pattern,$value);
                if($matches===false){WP_CLI::error('URL pattern scan failed.');}
                if($matches){$result['columns'][$index]['matching_cells']++;$result['columns'][$index]['old_origin_occurrences']+=$matches;$result['matching_cells']++;$result['old_origin_occurrences']+=$matches;$row_matches=true;}
            }
            $result['scanned_rows']++;
            if($row_matches){$result['matching_rows']++;}
        }
    }
    $after=$wpdb->get_row($summary_sql,ARRAY_A);
    if($wpdb->last_error || !is_array($after)){WP_CLI::error('Table size recheck failed.');}
    if($before!==$after || $result['scanned_rows']!==$row_count){$result['limit_reason']=$result['limit_reason']?:'table_changed_during_scan';}
    $result['scan_complete']=$result['limit_reason']===null;
}
// Diagnostics are not a transaction snapshot. A later migration must recheck.
WP_CLI::line('JDM_ARCHIVE_TABLE_REPORT:'.json_encode($result,JSON_UNESCAPED_SLASHES));
PHP
write_php table-diagnostic-public.php <<'PHP'
$r=json_decode(stream_get_contents(STDIN),true);
$keys=array('table','has_primary_key','row_count','columns','scan_complete','limit_reason','scanned_rows','scanned_bytes','old_origin_occurrences','matching_rows','matching_cells');
if(!is_array($r) || array_keys($r)!==$keys || !preg_match('/^wp_[A-Za-z0-9_]+$/D',$r['table']) || $r['has_primary_key']!==false || !is_bool($r['scan_complete']) || !in_array($r['limit_reason'],array(null,'table_size_limit','cell_or_byte_limit','table_changed_during_scan'),true) || !is_array($r['columns']) || count($r['columns'])>32){exit(1);}
foreach(array('row_count','scanned_rows','scanned_bytes','old_origin_occurrences','matching_rows','matching_cells') as $key){if(!is_int($r[$key]) || $r[$key]<0){exit(1);}}
foreach($r['columns'] as $c){
    if(!is_array($c) || array_keys($c)!==array('name','type','nullable','unique_key','auto_increment','old_origin_occurrences','matching_cells') || !preg_match('/^[A-Za-z0-9_]+$/D',$c['name']) || !preg_match('/^[a-z]+$/D',$c['type'])){exit(1);}
    foreach(array('nullable','unique_key','auto_increment') as $key){if(!is_bool($c[$key])){exit(1);}}
    foreach(array('old_origin_occurrences','matching_cells') as $key){if(!is_int($c[$key]) || $c[$key]<0){exit(1);}}
}
echo json_encode($r,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES),"\n";
PHP

audit() {
  local raw result
  raw="$("${WP[@]}" eval-file "$runtime_dir/audit.php" 2>/dev/null)" || fail 'WordPress read-only audit failed; raw output withheld.'
  result="$(printf '%s\n' "$raw" | sed -n 's/^JDM_ARCHIVE_REPORT://p')"
  printf '%s' "$result" | php "$runtime_dir/normalize-report.php" 2>/dev/null || fail 'Invalid sanitized audit result.'
}
# This mode executes only three bounded read-only probes. Raw output is never
# sent to the public report; private logs are owner-only and outside public_html.
if [[ "$MODE" == --diagnose ]]; then
  STAGE='diagnostic-private-log-directory'
  for executable in grep wc head; do command -v "$executable" >/dev/null 2>&1 || fail "Required diagnostic tool unavailable: $executable"; done
  command -v mktemp >/dev/null 2>&1 || fail 'mktemp is required for private diagnostics.'
  mkdir -p "$STATE_DIR"
  chmod 700 "$STATE_DIR"
  diagnostics_dir="$STATE_DIR/diagnostics"
  if [[ -e "$diagnostics_dir" || -L "$diagnostics_dir" ]]; then
    [[ -d "$diagnostics_dir" && ! -L "$diagnostics_dir" && "$(stat -c '%U' "$diagnostics_dir")" == "$ACCOUNT" ]] || fail 'Unexpected diagnostics directory.'
  fi
  mkdir -p "$diagnostics_dir"
  chmod 700 "$diagnostics_dir"
  diagnostic_run="$(mktemp -d "$diagnostics_dir/run.XXXXXXXX")"
  chmod 700 "$diagnostic_run"
  printf 'mode=diagnose\nprivate_logs=created\n'
  CLASSIFY_PHP=$(cat <<'PHP'
$stage = $argv[1];
$code = (int) $argv[2];
$out = file_get_contents($argv[3]);
$err = file_get_contents($argv[4]);
$marker = $argv[5];
$allowed_stages = array('eval_without_wordpress', 'wordpress_bootstrap', 'full_readonly_audit');
if (!in_array($stage, $allowed_stages, true)) { exit(1); }
$text = $err . "\n" . $out;
$rules = array(
    'config_hook_missing' => '/Configuration hook did not run/i',
    'wpdb_not_initialized' => '/(?:suppress_errors|get_var|get_col)\(\) on null/i',
    'unexpected_table_prefix' => '/Unexpected table prefix/i',
    'no_prefixed_tables' => '/No matching tables/i',
    'unexpected_table_identifier' => '/Unexpected table identifier/i',
    'database_query_failed' => '/Database audit failed/i',
    'database_connection_failed' => '/Error establishing a database connection|mysqli_real_connect|Connection refused|could not connect to (?:the )?(?:database|mysql)/i',
    'database_access_denied' => '/Access denied for user/i',
    'database_unavailable' => '/Unknown database|Unknown MySQL server host/i',
    'wp_not_installed' => '/not a WordPress installation|does not seem to be a WordPress installation|site you have requested is not installed|WordPress is not installed/i',
    'config_not_found' => '/wp-config\.php.*(?:not found|does not exist)|Could not find.*wp-config/i',
    'missing_mysql_extension' => '/missing.*MySQL extension|requires.*mysqli|mysqli.*not found/i',
    'cli_argument_error' => '/Parameter errors|unknown --|unknown parameter|not a registered wp command/i',
    'php_memory_limit' => '/Allowed memory size.*exhausted/i',
    'php_time_limit' => '/Maximum execution time.*exceeded/i',
    'php_parse_error' => '/Parse error|syntax error/i',
    'php_missing_function' => '/Call to undefined function/i',
    'php_missing_class' => '/Class [^\r\n]*not found/i',
    'php_undefined_constant' => '/Undefined constant/i',
    'php_type_error' => '/TypeError|must be of type/i',
    'filesystem_restriction' => '/open_basedir restriction/i',
    'filesystem_permission' => '/Permission denied/i',
    'php_fatal_error' => '/Fatal error|Uncaught (?:Error|Exception)/i',
);
$category = $code === 0 ? 'ok' : 'unclassified_failure';
foreach ($rules as $name => $pattern) {
    if (preg_match($pattern, $text)) { $category = $name; break; }
}
$components = array();
foreach (array(
    'must_use_plugin' => '/wp-content/mu-plugins/',
    'object_cache_dropin' => '/wp-content/object-cache.php',
    'database_dropin' => '/wp-content/db.php',
    'advanced_cache_dropin' => '/wp-content/advanced-cache.php',
    'wordpress_core' => '/wp-includes/',
    'wp_cli' => 'phar://',
) as $name => $needle) {
    if (strpos($text, $needle) !== false) { $components[] = $name; }
}
$present = strpos($out, $marker) !== false;
if ($code === 0 && !$present && $category === 'ok') { $category = 'expected_marker_missing'; }
$report = array(
    'stage' => $stage,
    'exit_code' => $code,
    'category' => $category,
    'expected_marker_present' => $present,
    'components_mentioned' => $components,
    'deprecation_notice_present' => (bool) preg_match('/Deprecated|Deprecation/i', $text),
    'warning_present' => (bool) preg_match('/Warning:/i', $text),
    'stdout_bytes' => strlen($out),
    'stderr_bytes' => strlen($err),
);
// Only typed, allowlisted fields from our bootstrap marker can be added.
if (in_array($stage, array('eval_without_wordpress', 'wordpress_bootstrap'), true) && preg_match('/^JDM_DIAG_(?:NO_WP|BOOTSTRAP):(.+)$/m', $out, $match)) {
    $data = json_decode($match[1], true);
    if (is_array($data) && isset($data['config_hook_present']) && is_bool($data['config_hook_present'])) {
        $report['config_hook_present'] = $data['config_hook_present'];
    }
    if (isset($data['php_version']) && is_string($data['php_version']) && preg_match('/^[0-9]+\.[0-9]+\.[0-9]+(?:[-+.][0-9A-Za-z.-]+)?$/D', $data['php_version'])) {
        $report['php_version'] = $data['php_version'];
    }
    if (isset($data['mysqli_available']) && is_bool($data['mysqli_available'])) {
        $report['mysqli_available'] = $data['mysqli_available'];
    }
}
echo json_encode($report, JSON_UNESCAPED_SLASHES), "\n";
PHP
)
  printf '%s\n' "$CLASSIFY_PHP" | write_php classifier.php
  # The reporter deliberately uses only shell tools. PHP configuration or a
  # failure to read private files cannot suppress the diagnostic result again.
  diagnostic_report() {
    local name="$1" code="$2" out="$3" err="$4" marker="$5" category='ok' present=false components='' stdout_bytes stderr_bytes
    local raw flags='' php_version='' hook_present='' mysqli_available=''
    case "$name" in eval_without_wordpress|wordpress_bootstrap|full_readonly_audit|php_classifier_probe) ;; *) fail 'Unexpected diagnostic stage.' ;; esac
    [[ "$code" =~ ^[0-9]+$ ]] || fail 'Unexpected diagnostic exit code.'
    [[ "$code" == 0 ]] || category='unclassified_failure'
    if grep -Eiq 'Configuration hook did not run' "$err" "$out"; then category='config_hook_missing'
    elif grep -Eiq 'Undefined variable.*argv|Undefined array key.*argv' "$err" "$out"; then category='cli_argv_unavailable'
    elif grep -Eiq 'open_basedir restriction' "$err" "$out"; then category='filesystem_open_basedir'
    elif grep -Eiq 'Call to undefined function.*file_get_contents' "$err" "$out"; then category='php_file_read_unavailable'
    elif grep -Eiq 'Permission denied' "$err" "$out"; then category='filesystem_permission'
    elif grep -Eiq 'suppress_errors\(\) on null|get_var\(\) on null|get_col\(\) on null' "$err" "$out"; then category='wpdb_not_initialized'
    elif grep -Eiq 'Unexpected table prefix' "$err" "$out"; then category='unexpected_table_prefix'
    elif grep -Eiq 'No matching tables' "$err" "$out"; then category='no_prefixed_tables'
    elif grep -Eiq 'Unexpected table identifier' "$err" "$out"; then category='unexpected_table_identifier'
    elif grep -Eiq 'Database audit failed' "$err" "$out"; then category='database_query_failed'
    elif grep -Eiq 'Error establishing a database connection|mysqli_real_connect|Connection refused' "$err" "$out"; then category='database_connection_failed'
    elif grep -Eiq 'Access denied for user' "$err" "$out"; then category='database_access_denied'
    elif grep -Eiq 'Unknown database|Unknown MySQL server host' "$err" "$out"; then category='database_unavailable'
    elif grep -Eiq 'not a WordPress installation|does not seem to be a WordPress installation|site you have requested is not installed|WordPress is not installed' "$err" "$out"; then category='wp_not_installed'
    elif grep -Eiq 'wp-config.php.*not found|wp-config.php.*does not exist|Could not find.*wp-config' "$err" "$out"; then category='config_not_found'
    elif grep -Eiq 'missing.*MySQL extension|requires.*mysqli|mysqli.*not found' "$err" "$out"; then category='missing_mysql_extension'
    elif grep -Eiq 'Parameter errors|unknown --|unknown parameter|not a registered wp command' "$err" "$out"; then category='cli_argument_error'
    elif grep -Eiq 'Allowed memory size.*exhausted' "$err" "$out"; then category='php_memory_limit'
    elif grep -Eiq 'Maximum execution time.*exceeded' "$err" "$out"; then category='php_time_limit'
    elif grep -Eiq 'Parse error|syntax error' "$err" "$out"; then category='php_parse_error'
    elif grep -Eiq 'Call to undefined function' "$err" "$out"; then category='php_missing_function'
    elif grep -Eiq 'Class .*not found' "$err" "$out"; then category='php_missing_class'
    elif grep -Eiq 'Undefined constant' "$err" "$out"; then category='php_undefined_constant'
    elif grep -Eiq 'TypeError|must be of type' "$err" "$out"; then category='php_type_error'
    elif grep -Eiq 'Fatal error|Uncaught Error|Uncaught Exception' "$err" "$out"; then category='php_fatal_error'
    fi
    if grep -Fq -- "$marker" "$out"; then present=true; fi
    if [[ "$code" == 0 && "$present" == false && "$category" == ok ]]; then category='expected_marker_missing'; fi
    for component in must_use_plugin object_cache_dropin database_dropin advanced_cache_dropin wordpress_core wp_cli; do
      local needle=''
      case "$component" in
        must_use_plugin) needle='/wp-content/mu-plugins/' ;;
        object_cache_dropin) needle='/wp-content/object-cache.php' ;;
        database_dropin) needle='/wp-content/db.php' ;;
        advanced_cache_dropin) needle='/wp-content/advanced-cache.php' ;;
        wordpress_core) needle='/wp-includes/' ;;
        wp_cli) needle='phar://' ;;
      esac
      if grep -Fq -- "$needle" "$err" "$out"; then components+="${components:+,}\"$component\""; fi
    done
    stdout_bytes="$(wc -c < "$out")"; stdout_bytes="${stdout_bytes//[[:space:]]/}"
    stderr_bytes="$(wc -c < "$err")"; stderr_bytes="${stderr_bytes//[[:space:]]/}"
    local deprecated=false warning=false
    if grep -Eiq 'Deprecated|Deprecation' "$err" "$out"; then deprecated=true; fi
    if grep -Fq 'Warning:' "$err" "$out"; then warning=true; fi
    printf '{"stage":"%s","exit_code":%s,"category":"%s","expected_marker_present":%s,"components_mentioned":[%s],"deprecation_notice_present":%s,"warning_present":%s,"stdout_bytes":%s,"stderr_bytes":%s' "$name" "$code" "$category" "$present" "$components" "$deprecated" "$warning" "$stdout_bytes" "$stderr_bytes"
    # Extract only tightly constrained values from our own runtime marker. No
    # raw line, exception message, path or arbitrary JSON string is printed.
    if [[ "$name" == eval_without_wordpress || "$name" == wordpress_bootstrap ]]; then
      raw="$(grep -E '^JDM_DIAG_(NO_WP|BOOTSTRAP):' "$out" | head -n1 || true)"
      local version_pattern='"php_version":"([0-9]+\.[0-9]+\.[0-9]+([-+][0-9A-Za-z.-]+)?)"'
      local hook_pattern='"config_hook_present":(true|false)'
      local mysqli_pattern='"mysqli_available":(true|false)'
      if [[ "$raw" =~ $version_pattern ]]; then printf ',"php_version":"%s"' "${BASH_REMATCH[1]}"; fi
      if [[ "$raw" =~ $hook_pattern ]]; then printf ',"config_hook_present":%s' "${BASH_REMATCH[1]}"; fi
      if [[ "$raw" =~ $mysqli_pattern ]]; then printf ',"mysqli_available":%s' "${BASH_REMATCH[1]}"; fi
    fi
    printf '}\n'
  }

  diagnostic_probe() {
    local name="$1" marker="$2" code
    shift 2
    STAGE="diagnostic-$name"
    if "${WP[@]}" "$@" >"$diagnostic_run/$name.stdout.log" 2>"$diagnostic_run/$name.stderr.log"; then
      code=0
    else
      code=$?
    fi
    chmod 600 "$diagnostic_run/$name.stdout.log" "$diagnostic_run/$name.stderr.log"
    diagnostic_report "$name" "$code" "$diagnostic_run/$name.stdout.log" "$diagnostic_run/$name.stderr.log" "$marker"
    # Reproduce the previous reporting failure once, but classify it with shell
    # tools and keep its raw stderr private. Its failure never stops the probes.
    if [[ "$name" == eval_without_wordpress ]]; then
      local classifier_code
      if php -d display_errors=stderr -d log_errors=0 -d html_errors=0 "$runtime_dir/classifier.php" "$name" "$code" "$diagnostic_run/$name.stdout.log" "$diagnostic_run/$name.stderr.log" "$marker" >"$diagnostic_run/php_classifier_probe.stdout.log" 2>"$diagnostic_run/php_classifier_probe.stderr.log"; then classifier_code=0; else classifier_code=$?; fi
      chmod 600 "$diagnostic_run/php_classifier_probe.stdout.log" "$diagnostic_run/php_classifier_probe.stderr.log"
      diagnostic_report php_classifier_probe "$classifier_code" "$diagnostic_run/php_classifier_probe.stdout.log" "$diagnostic_run/php_classifier_probe.stderr.log" '"category"'
    fi
  }
  diagnostic_probe eval_without_wordpress JDM_DIAG_NO_WP: eval-file "$runtime_dir/diagnostic-eval-without-wordpress.php" --skip-wordpress
  diagnostic_probe wordpress_bootstrap JDM_DIAG_BOOTSTRAP: eval-file "$runtime_dir/diagnostic-wordpress-bootstrap.php"
  diagnostic_probe full_readonly_audit JDM_ARCHIVE_REPORT: eval-file "$runtime_dir/audit.php"
  printf 'result=read_only_diagnostics_complete\nraw_log_content=private_only\n'
  exit 0
fi

report="$(audit)"
if [[ "$MODE" == --diagnose-table ]]; then
  STAGE='read-only-table-diagnostic'
  printf '%s' "$report" | php "$runtime_dir/table-diagnostic-guard.php" 2>/dev/null || fail 'Table diagnostic requires exactly the known single no-primary-key blocker and the old site URL.'
  "${WP[@]}" eval-file "$runtime_dir/diagnose-table.php" >"$runtime_dir/table.stdout.log" 2>"$runtime_dir/table.stderr.log" || fail 'Read-only table diagnostic failed; raw logs remain private.'
  sed -n 's/^JDM_ARCHIVE_TABLE_REPORT://p' "$runtime_dir/table.stdout.log" | php "$runtime_dir/table-diagnostic-public.php" 2>/dev/null || fail 'Invalid sanitized table diagnostic result.'
  printf 'mode=diagnose-table\nresult=read_only_table_diagnostic_complete\n'
  exit 0
fi
# Public-safe report excludes even non-secret database identity/table fingerprints.
printf '%s' "$report" | php "$runtime_dir/public-report.php"
blockers="$(printf '%s' "$report" | php "$runtime_dir/count-blockers.php")"
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
printf '%s' "$report" | php "$runtime_dir/reject-existing-archive.php" || fail 'WordPress is already using the archive origin.'
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
printf '%s' "$archive_identity" | php "$runtime_dir/verify-archive-identity.php" || fail 'The archive alias has not been verified as this old WordPress; no changes made.'
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
printf '%s' "$report" | php "$runtime_dir/prepare-state.php" > "$state_tmp"
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
"${WP[@]}" eval-file "$runtime_dir/invalidate-cache.php" >/dev/null 2>&1 || fail 'Scoped cache invalidation failed; inspect the archive before retrying.'
STAGE='postflight'
after="$(audit)"
printf '%s\n%s' "$report" "$after" | php "$runtime_dir/verify-postflight.php" || fail 'Postflight mismatch; review private state before any further changes.'
remaining="$(search_count "$OLD_PATTERN" "$ARCHIVE" --dry-run)"
[[ "$remaining" == 0 ]] || fail 'Old origin references remain outside GUID; inspect before retrying.'
php "$runtime_dir/complete-state.php" "$STATE"
printf 'mode=apply\nresult=archive_configured\narchive=%s\noriginal_settings=%s\n' "$ARCHIVE" "$STATE"
printf 'Next: verify archive HTML, assets, login, redirects and X-Robots-Tag over HTTPS; purge only this site’s page/hosting cache if necessary.\n'
