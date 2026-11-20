<?php
declare(strict_types=1);
namespace LombardCatalog;

function transferFrame($input,int $limit): array {
    $line=fgets($input,$limit+2);
    if ($line===false || !str_ends_with($line,"\n") || strlen($line)>$limit) fail('source_incomplete');
    $data=json_decode($line,true,64,JSON_THROW_ON_ERROR);
    if (!is_array($data)) fail('source_format');
    return $data;
}
function transferReply($output,array $data): void {
    $line=json_encode($data,JSON_THROW_ON_ERROR)."\n";$offset=0;
    while ($offset<strlen($line)) {
        $written=fwrite($output,substr($line,$offset));
        if ($written===false || $written===0) fail('connection_lost');
        $offset+=$written;
    }
    if (!fflush($output)) fail('connection_lost');
}
function transferredImageType(string $bytes): string {
    $info=@getimagesizefromstring($bytes);
    if (!$info || $info[0]<1 || $info[1]<1 || $info[0]>16000 || $info[1]>16000 || $info[0]*$info[1]>80000000) fail('source_image');
    return match($info['mime']) {'image/jpeg'=>'jpg','image/png'=>'png','image/webp'=>'webp',default=>throw new Failure('source_image')};
}
function receiveCatalog(App $app,$input,$output): void {
    locked($app->base.'/data/sync.lock',function() use($app,$input,$output): void {
      try {
        if (!$app->config()['enabled']) { transferReply($output,['result'=>'disabled']); return; }
        $old=$app->snapshot();validateProducts($app,$old['products']);
        transferReply($output,['ready'=>'sezam-public-offers-v1']);
        $m=transferFrame($input,25000000);$rows=$m['products']??null;
        if (array_diff_key($m,array_flip(['format','source','checked_on','currency','count','products'])) ||
            ($m['format']??'')!=='sezam-public-offers-v1' || ($m['source']??'')!=='sezam.com.pl' || ($m['currency']??'')!=='PLN' ||
            !is_array($rows) || !array_is_list($rows) || count($rows)>50000 || ($m['count']??null)!==count($rows)) fail('source_format');
        $date=validDate($m['checked_on']??null);
        if ($date<($old['source_checked_on']??'')) fail('source_older');
        $paths=[];$need=[];$totalBytes=0;
        if (is_link($app->public.'/assets') || !is_dir($app->public.'/assets')) fail('source_image');
        $previous=[];$slugs=[];
        foreach ($old['products'] as $p) { $id=strtoupper($p['source_id']);$previous[$id]=$p;$slugs[$p['slug']]=$id; }
        $seen=[];$products=[];
        $fields=array_flip(['slug','name','category','status','source_id','source_url','description','price','checked_on','price_valid_until','olx_id','images']);
        foreach ($rows as $row) {
            if (!is_array($row) || array_diff_key($row,$fields)) fail('source_format');
            validateProductFields($row);
            $id=strtoupper($row['source_id']);
            if (isset($seen[$id])) fail('source_duplicate');
            $seen[$id]=true;
            if (isset($previous[$id])) $row['slug']=$previous[$id]['slug'];
            elseif (isset($slugs[$row['slug']])) $row['slug'].='-'.strtolower($id);
            if (strlen($row['slug'])>230 || (isset($slugs[$row['slug']]) && $slugs[$row['slug']]!==$id)) fail('source_duplicate');
            $slugs[$row['slug']]=$id;
            if ($row['checked_on']>$date || $row['checked_on']<($previous[$id]['checked_on']??'')) fail('source_older');
            if (!is_array($row['images']??null) || !array_is_list($row['images']) || !$row['images'] || count($row['images'])>30) fail('source_image');
            foreach ($row['images'] as $digest) {
                if (!is_string($digest) || !preg_match('/^[a-f0-9]{64}$/D',$digest)) fail('source_image');
                if (isset($paths[$digest]) || isset($need[$digest])) continue;
                foreach (['jpg','png','webp'] as $ext) {
                    $path='/assets/sales-feed-'.$digest.'.'.$ext;
                    if (!is_link($app->public.$path) && is_file($app->public.$path) && hash_file('sha256',$app->public.$path)===$digest) { $paths[$digest]=$path;break; }
                }
                if (!isset($paths[$digest])) $need[$digest]=true;
                if (count($paths)+count($need)>50000) fail('source_image_limit');
            }
            $products[]=$row;
        }
        transferReply($output,['missing'=>array_keys($need)]);
        foreach ($need as $digest=>$_) {
            $frame=transferFrame($input,16000200);
            if (array_diff_key($frame,array_flip(['sha256','data'])) || ($frame['sha256']??'')!==$digest || !is_string($frame['data']??null)) fail('source_image');
            $bytes=base64_decode($frame['data'],true);
            if ($bytes===false || strlen($bytes)>12000000 || hash('sha256',$bytes)!==$digest) fail('source_image');
            $totalBytes+=strlen($bytes);if ($totalBytes>1024*1024*1024) fail('source_image_limit');
            $path='/assets/sales-feed-'.$digest.'.'.transferredImageType($bytes);
            atomic($app->public.$path,$bytes,0644);$paths[$digest]=$path;unset($frame,$bytes);
        }
        if (transferFrame($input,128)!==['complete'=>true]) fail('source_incomplete');
        foreach ($products as &$p) { $p['images']=array_map(fn($digest)=>$paths[$digest],$p['images']);$p['image']=$p['images'][0]; }
        unset($p);
        foreach ($previous as $id=>$p) if (!isset($seen[$id])) { $p['status']='unavailable';$products[]=$p; }
        validateProducts($app,$products);$now=gmdate('c');
        $snapshot=['products'=>$products,'source_checked_on'=>$date,'ingested_from'=>'https://sezam.com.pl/na-sprzedaz/','synced_at'=>$now];
        if ($old['products']!==$products || ($old['source_checked_on']??'')!==$date) publishCatalog($app,$snapshot);
        $active=count(array_filter($products,fn($p)=>in_array($p['status'],['in_stock','reserved'],true)));
        $status=['result'=>'ok','count'=>count($rows),'active_count'=>$active,'images'=>count($paths),'copied'=>count($need),'source_checked_on'=>$date,'last_attempt'=>$now,'last_success'=>$now];
        jsonWrite($app->base.'/data/status.json',$status);
        transferReply($output,['result'=>'ok','count'=>count($rows),'active_count'=>$active,'images'=>count($paths),'copied'=>count($need),'source_checked_on'=>$date,'last_success'=>$now]);
      } catch (\Throwable $error) {
        // Record failure before releasing the synchronization lock, so an older
        // failed attempt cannot overwrite the status of a newer successful one.
        try {$status=jsonRead($app->base.'/data/status.json');$status['result']='error';$status['error']=$error instanceof Failure?$error->getMessage():'receiver_error';$status['last_attempt']=gmdate('c');jsonWrite($app->base.'/data/status.json',$status);}catch(\Throwable){}
        throw $error;
      }
    });
}
