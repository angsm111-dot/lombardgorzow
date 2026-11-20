<?php
declare(strict_types=1);
// Reviewed CLI-only one-shot operations. Reports contain public metadata only.
namespace SezamCatalogOps;

const SOURCE_HOME='/home/molo11';
const EXCHANGE=SOURCE_HOME.'/private/sezam-catalog-transfer';
const TARGET='lombardgorzow.com';
const DEPENDENCIES=[
    'bootstrap-lombardgorzow.php'=>'02814f6bad0b894d26b5c61f6e5de7e68710a9a8d2e3af6725230c316dfc8636',
    'send-lombardgorzow.php'=>'33ba90f2e61e9be1fd9429dc6af505d1cee5dc215949799c29d26e525700cc70',
    // Exact GitHub blob c51c951a3a297afea4f9a142c5fdd994e9cd9a57 (no extra reference-snapshot LF).
    'send.php'=>'1cf985ab762d945bedd9a133373700243e41b09e7a19044084a7fbd5644b0056',
];
const ERROR_CODES=['arguments_invalid','account_mismatch','path_invalid','dependency_mismatch','ops_busy','operation_failed',
    'receiver_readiness_required','sender_not_ready','host_pin_invalid','host_pin_missing','host_pin_mismatch','host_pin_unverified','host_pin_changed',
    'cron_read_failed','cron_install_failed','existing_sender_required','payload_missing','unsafe_directory','unsafe_file','write_failed','lock_failed',
    'process_failed','process_output_invalid','incomplete_identity','key_generation_failed','public_key_invalid','cron_path_invalid','bootstrap_failed',
    'delivery_failed','sender_failed','receipt_invalid','report_failed'];
final class DependencyMismatch extends \RuntimeException {
    public function __construct(public readonly string $dependencyName,public readonly string $expectedSha256,public readonly ?string $actualSha256) {
        parent::__construct('dependency_mismatch');
    }
}
function fail(string $reason): never { throw new \RuntimeException($reason); }
function safeError(\Throwable $error): string {
    return $error instanceof \RuntimeException && in_array($error->getMessage(),ERROR_CODES,true) ? $error->getMessage() : 'operation_failed';
}
function arguments(array $argv): array {
    $mode=null;$nonce=null;$ready=false;
    foreach(array_slice($argv,1) as $value) {
        if(in_array($value,['--prepare','--verify-host','--enable','--check'],true) && $mode===null) $mode=substr($value,2);
        elseif(is_string($value) && preg_match('/^--nonce=([a-f0-9]{32})$/D',$value,$match) && $nonce===null) $nonce=$match[1];
        elseif($value==='--receiver-ready=23048' && !$ready) $ready=true;
        else fail('arguments_invalid');
    }
    if($mode===null || $nonce===null || ($ready && $mode!=='enable')) fail('arguments_invalid');
    if($mode==='enable' && !$ready) fail('receiver_readiness_required');
    return ['operation'=>$mode,'nonce'=>$nonce,'receiver_ready'=>$ready];
}
function guardedPaths(): void {
    foreach([SOURCE_HOME,SOURCE_HOME.'/private',EXCHANGE,SOURCE_HOME.'/public_html'] as $path) {
        if(is_link($path) || !is_dir($path) || realpath($path)!==$path) fail('path_invalid');
    }
    $owner=fileowner(SOURCE_HOME);
    if($owner===false || getmyuid()!==$owner || (function_exists('posix_geteuid') && posix_geteuid()!==$owner)) fail('account_mismatch');
    if(realpath(__DIR__)!==EXCHANGE || is_link(__FILE__) || fileowner(__FILE__)!==$owner) fail('path_invalid');
}
function privateDirectory(string $path): void {
    if(is_link($path) || (file_exists($path) && !is_dir($path))) fail('path_invalid');
    if(!is_dir($path) && !mkdir($path,0700)) fail('write_failed');
    if(fileowner($path)!==fileowner(SOURCE_HOME) || !chmod($path,0700)) fail('account_mismatch');
}
function loadReviewedBootstrap(): array {
    $checks=[];
    foreach(DEPENDENCIES as $name=>$hash) {
        $path=EXCHANGE.'/'.$name;
        $actual=null;
        if(!is_link($path) && is_file($path) && filesize($path)<=250000) {
            $digest=hash_file('sha256',$path);
            if(is_string($digest) && preg_match('/^[a-f0-9]{64}$/D',$digest)) $actual=$digest;
        }
        if($actual===null || !hash_equals($hash,$actual)) throw new DependencyMismatch($name,$hash,$actual);
        $checks[]=['dependency_name'=>$name,'expected_sha256'=>$hash,'actual_sha256'=>$actual];
    }
    require_once EXCHANGE.'/bootstrap-lombardgorzow.php';
    return $checks;
}
/** Injectable invocation makes the no-implicit-enable and failure cases testable offline. */
function operate(array $args,callable $invoke): array {
    $operation=$args['operation'];
    if($operation!=='enable') return $invoke('--'.$operation);
    if(!$args['receiver_ready']) fail('receiver_readiness_required');
    $check=$invoke('--check');
    if(($check['result']??'')!=='checked' || ($check['identity_ready']??false)!==true || ($check['host_pin_ready']??false)!==true || ($check['schedule_installed']??false)!==true) fail('sender_not_ready');
    $pin=$invoke('--verify-host');
    if(($pin['result']??'')!=='verified') fail('host_pin_unverified');
    $result=$invoke('--enable'); // Protocol requires the receiver's ready greeting and full matching receipt.
    $result['receiver_receipt_verified']=($result['result']??'')==='ok' && ($result['enabled']??false)===true;
    return $result;
}
function publicStatus(array $value): array {
    $out=[];
    if(isset($value['result']) && in_array($value['result'],['prepared','verified','checked','ok','waiting','busy','error','disabled'],true)) $out['result']=$value['result'];
    foreach(['enabled','identity_ready','host_pin_ready','schedule_installed','receiver_receipt_verified'] as $key) if(is_bool($value[$key]??null)) $out[$key]=$value[$key];
    foreach(['count','active_count','images','copied','managed_schedule_count'] as $key) if(is_int($value[$key]??null) && $value[$key]>=0 && $value[$key]<=1500000) $out[$key]=$value[$key];
    foreach(['last_success','attempted_at'] as $key) if(is_string($value[$key]??null) && preg_match('/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$/D',$value[$key])) $out[$key]=$value[$key];
    if(is_string($value['source_checked_on']??null) && preg_match('/^\d{4}-\d{2}-\d{2}$/D',$value['source_checked_on'])) $out['source_checked_on']=$value['source_checked_on'];
    if(is_string($value['error']??null) && in_array($value['error'],ERROR_CODES,true)) $out['error']=$value['error'];
    if(($out['schedule_installed']??false)===true && ($value['schedule']??null)==='17,47 * * * *') $out['schedule']='17,47 * * * *';
    if(isset($value['schedule_reason']) && in_array($value['schedule_reason'],['verified','missing','multiple_entries','unexpected_entry'],true)) $out['schedule_reason']=$value['schedule_reason'];
    return $out;
}
function publicReport(array $args,array $value): array {
    $out=['schema'=>1,'source'=>'sezam.com.pl','target'=>TARGET,'operation'=>$args['operation'],'nonce'=>$args['nonce'],'reported_at'=>gmdate('c')]+publicStatus($value);
    if($args['operation']==='prepare' && is_string($value['public_key']??null) && preg_match('/^ssh-ed25519 [A-Za-z0-9+\/]{68}$/D',$value['public_key'])) $out['public_key']=$value['public_key'];
    if($args['operation']==='check' && is_array($value['status']??null)) $out['status']=publicStatus($value['status']);
    if($args['operation']==='enable') $out['receiver_readiness_confirmed_by_operator']=$args['receiver_ready'];
    // Only fixed public PHP dependencies may be identified; never report paths or bytes.
    $name=$value['dependency_name']??null;
    if(($value['error']??'')==='dependency_mismatch' && is_string($name) && isset(DEPENDENCIES[$name])
        && ($value['expected_sha256']??'')===DEPENDENCIES[$name]) {
        $out['dependency_name']=$name;$out['expected_sha256']=DEPENDENCIES[$name];
        $actual=$value['actual_sha256']??null;
        $out['actual_sha256']=is_string($actual) && preg_match('/^[a-f0-9]{64}$/D',$actual)?$actual:null;
    }
    if(isset($value['dependency_checks']) && is_array($value['dependency_checks']) && array_is_list($value['dependency_checks']) && count($value['dependency_checks'])<=count(DEPENDENCIES)) {
        $checks=[];$seen=[];
        foreach($value['dependency_checks'] as $item) {
            if(!is_array($item))continue;
            $name=$item['dependency_name']??null;$actual=$item['actual_sha256']??null;
            if(!is_string($name) || !isset(DEPENDENCIES[$name]) || isset($seen[$name]) || ($item['expected_sha256']??null)!==DEPENDENCIES[$name]
                || !is_string($actual) || !preg_match('/^[a-f0-9]{64}$/D',$actual))continue;
            $seen[$name]=true;$checks[]=['dependency_name'=>$name,'expected_sha256'=>DEPENDENCIES[$name],'actual_sha256'=>$actual,'matched'=>hash_equals(DEPENDENCIES[$name],$actual)];
        }
        $out['dependency_checks']=$checks;
    }
    return $out;
}
function publishReport(string $nonce,array $report): void {
    $target=SOURCE_HOME.'/public_html/sezam-catalog-ops-'.$nonce.'.json';
    if(is_link($target) || (file_exists($target) && !is_file($target))) fail('report_failed');
    $tmp=SOURCE_HOME.'/public_html/.sezam-catalog-report-'.$nonce.'-'.bin2hex(random_bytes(6)).'.tmp';
    $stream=fopen($tmp,'xb');if(!$stream) fail('report_failed');
    try {
        $bytes=json_encode($report,JSON_THROW_ON_ERROR|JSON_UNESCAPED_SLASHES)."\n";$offset=0;
        while($offset<strlen($bytes)) {$n=fwrite($stream,substr($bytes,$offset));if(!$n)fail('report_failed');$offset+=$n;}
        if(!fflush($stream) || !chmod($tmp,0644)) fail('report_failed');
        fclose($stream);$stream=null;
        if(!rename($tmp,$target)) fail('report_failed');
    } finally {if(is_resource($stream))fclose($stream);if(is_file($tmp))unlink($tmp);}
}
function main(array $argv): int {
    $args=arguments($argv);guardedPaths();
    $state=EXCHANGE.'/lombardgorzow';privateDirectory($state);privateDirectory($state.'/ops');
    $claim=$state.'/ops/'.$args['nonce'].'.claimed';
    if(is_link($claim) || (file_exists($claim) && !is_file($claim))) fail('path_invalid');
    if(is_file($claim)) return 0; // A repeated panel cron never repeats an operation or overwrites its report.
    $handle=fopen($claim,'x');if(!$handle)return 0;
    fwrite($handle,json_encode(['operation'=>$args['operation'],'claimed_at'=>gmdate('c')],JSON_THROW_ON_ERROR));fclose($handle);chmod($claim,0600);
    $lockPath=$state.'/ops/operation.lock';
    if(is_link($lockPath) || (file_exists($lockPath) && !is_file($lockPath))) fail('path_invalid');
    $lock=fopen($lockPath,'c');$locked=false;
    try {
        if(!$lock || !($locked=flock($lock,LOCK_EX|LOCK_NB))) fail('ops_busy');
        chmod($lockPath,0600);$checks=loadReviewedBootstrap();
        $result=operate($args,fn(string $mode): array => \SezamCatalogTarget\bootstrap(['bootstrap-lombardgorzow.php',$mode]));
        $result['dependency_checks']=$checks;
    } catch(\Throwable $error) {
        $result=['result'=>'error','error'=>safeError($error)];
        if($error instanceof DependencyMismatch) $result+=['dependency_name'=>$error->dependencyName,'expected_sha256'=>$error->expectedSha256,'actual_sha256'=>$error->actualSha256];
    }
    finally {if(is_resource($lock)){if($locked)flock($lock,LOCK_UN);fclose($lock);}}
    publishReport($args['nonce'],publicReport($args,$result));
    return ($result['result']??'')==='error'?1:0;
}
if(realpath($_SERVER['SCRIPT_FILENAME']??'')===__FILE__) {
    if(PHP_SAPI!=='cli'){http_response_code(404);exit;}
    umask(0077);ini_set('display_errors','0');ini_set('log_errors','0');
    try {exit(main($argv));} catch(\Throwable $error) {echo json_encode(['schema'=>1,'result'=>'error','error'=>safeError($error)],JSON_THROW_ON_ERROR)."\n";exit(1);}
}
