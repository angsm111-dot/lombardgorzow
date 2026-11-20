<?php
declare(strict_types=1);
namespace LombardCatalog;

function html(mixed $value): string { return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }
function available(array $p): bool { return in_array($p['status'] ?? '', ['in_stock', 'reserved'], true); }
function matchesCategory(array $p, string $category): bool {
    if ($category === '') return true;
    $stored = $p['category'] ?? '';
    if ($category === 'bizuteria') return in_array($stored, ['bizuteria','pierscionki'], true);
    if ($category === 'pierscionki') return $stored === 'pierscionki' || ($stored === 'bizuteria' && preg_match('/\b(?:pierścion(?:ek|ki|ka)|pierscion(?:ek|ki|ka)|sygnet(?:y|em|u)?)\b/iu', (string)($p['name'] ?? '')) === 1);
    return $stored === $category;
}
function productPath(array $p): string { return '/na-sprzedaz/'.$p['slug'].'/'; }
function catalogReadDate(array $snapshot): ?string {
    $value = $snapshot['source_checked_on'] ?? null;
    return is_string($value) && preg_match('/^\d{4}-\d{2}-\d{2}$/D', $value) ? $value : null;
}
function publicProducts(array $products): array {
    $fields = array_flip(['slug','name','category','status','source_id','source_url','description','price','checked_on','image','images']);
    return array_map(fn(array $p): array => array_intersect_key($p, $fields), $products);
}
function siteMetadata(App $app): array {
    $site = jsonRead($app->base.'/public-site.json');
    if (($site['origin'] ?? '') !== 'https://lombardgorzow.com' || !is_string($site['name'] ?? null) || !is_string($site['address'] ?? null)
        || !is_string($site['whatsapp'] ?? null) || !preg_match('/^[0-9]{9,15}$/D', $site['whatsapp'])
        || !preg_match('~^https://www\.olx\.pl/oferty/uzytkownik/[A-Za-z0-9]+/$~D', $site['olx_profile'] ?? '')) throw new \RuntimeException('site_config_invalid');
    return $site;
}
function offerCount(int $n): string {
    return $n.' '.($n === 1 ? 'oferta' : (in_array($n % 10,[2,3,4],true) && !in_array($n % 100,[12,13,14],true) ? 'oferty' : 'ofert'));
}
function priceLabel(mixed $price): string { return number_format((float)$price, 2, ',', "\u{00a0}").' zł'; }
function statusLabel(array $p): string {
    return match ($p['status']) { 'in_stock' => 'Dostępna oferta', 'reserved' => 'Zarezerwowany', default => 'Oferta niedostępna' };
}
function salesActions(array $site): string {
    return '<div class="sales-actions"><a class="btn btn-dark" href="'.html($site['olx_profile']).'" target="_blank" rel="noopener noreferrer">Zobacz ogłoszenia OLX <span aria-hidden="true">↗</span></a><a class="text-link" href="https://wa.me/'.html($site['whatsapp']).'" target="_blank" rel="noopener noreferrer">Zapytaj na WhatsApp <span aria-hidden="true">→</span></a></div>';
}
function salesSidebar(array $products, string $selected): string {
    $active = array_values(array_filter($products, __NAMESPACE__.'\\available'));
    $out = '<aside class="sales-sidebar"><h2>Kategorie</h2><nav class="sales-categories" aria-label="Kategorie przedmiotów">';
    foreach (['' => 'Wszystkie przedmioty'] + CATEGORIES as $key => $label) {
        $count = count(array_filter($active, fn(array $p): bool => matchesCategory($p, $key)));
        if ($key !== '' && !$count && $key !== $selected) continue;
        $out .= '<a href="/na-sprzedaz/'.($key === '' ? '' : $key.'/').'"'.($key === $selected ? ' aria-current="page"' : '').'><span>'.html($label).'</span><span class="sales-count" aria-label="'.offerCount($count).'">'.$count.'</span></a>';
    }
    return $out.'</nav></aside>';
}
function salesCard(array $p): string {
    return '<article class="sales-card"><a href="'.html(productPath($p)).'"><div class="sales-image"><img src="'.html($p['image']).'" alt="'.html($p['name']).'" loading="lazy" decoding="async" width="600" height="600"></div><h3>'.html($p['name']).'</h3></a><p class="sales-status">'.statusLabel($p).'</p><strong>'.priceLabel($p['price']).'</strong></article>';
}
function loadTemplate(App $app): string {
    foreach ([$app->public.'/assets/sales-template.html', $app->base.'/template.html'] as $path) {
        if (is_link($path) || !is_file($path) || filesize($path) > 2000000) continue;
        $template = file_get_contents($path);
        if (is_string($template) && str_contains($template, '<!-- SEZAM_SALES_TEMPLATE_V1 -->')
            && substr_count($template, '<main id="main">') === 1 && substr_count($template, '</main>') === 1 && substr_count($template, '<title>') === 1) return $template;
    }
    throw new \RuntimeException('template_invalid');
}
function renderCatalog(App $app, array $snapshot, string $route = ''): string {
    $products = $snapshot['products'] ?? [];
    validateProducts($app, $products);
    $site = siteMetadata($app);
    $template = loadTemplate($app);
    $listing = $route === '' || isset(CATEGORIES[$route]);
    $canonical = $site['origin'].'/na-sprzedaz/'.($route === '' ? '' : $route.'/');
    $title = $route === '' ? 'Na sprzedaż — Lombard SEZAM Gorzów' : (($listing ? CATEGORIES[$route] : 'Przedmiot').' — Lombard SEZAM Gorzów');
    $description = 'Przedmioty na sprzedaż w Lombardzie SEZAM przy Pocztowej 11 w Gorzowie. Zobacz ceny, zdjęcia i zapytaj o dostępność.';
    $schema = ''; $ogImage = null;
    $crumbs = '<nav class="breadcrumbs wrap" aria-label="Ścieżka nawigacji"><a href="/">Strona główna</a><span aria-hidden="true">/</span>';
    if ($route !== '') $crumbs .= '<a href="/na-sprzedaz/">Na sprzedaż</a><span aria-hidden="true">/</span>';
    if ($listing) {
        $selected = $route === '' ? 'Wszystkie przedmioty' : CATEGORIES[$route];
        $crumbs .= '<span aria-current="page">'.html($route === '' ? 'Na sprzedaż' : $selected).'</span></nav>';
        $heading = $route === '' ? 'Znajdź coś<br><em>dla siebie.</em>' : html($selected).'<br><em>w SEZAM.</em>';
        $content = '<section class="section wrap sales-section"><div class="sales-heading"><span class="eyebrow muted">PRZEDMIOTY Z DOBRĄ HISTORIĄ</span><h1>'.$heading.'</h1><p>Biżuteria, zegarki i sprzęt, które mogą zyskać nowego właściciela. Zobacz nasze ogłoszenia i zapytaj o wybrany przedmiot.</p></div><div class="sales-layout">'.salesSidebar($products,$route).'<div class="sales-results"><div class="sales-results-heading"><h2>'.html($selected).'</h2>';
        $items = array_values(array_filter($products, fn(array $p): bool => available($p) && matchesCategory($p,$route)));
        $content .= '<p>'.offerCount(count($items)).'</p></div>';
        $date = catalogReadDate($snapshot);
        if ($date !== null) $content .= '<p class="sales-date">Dane ofert z dnia '.html($date).'. Przed zakupem potwierdź aktualną cenę i dostępność.</p>';
        if ($items) {
            $content .= '<div class="sales-grid">';
            foreach ($items as $p) $content .= salesCard($p);
            $content .= '</div>';
        } else $content .= '<div class="sales-empty"><h3>Zapytaj o aktualną ofertę.</h3><p>W tej kategorii nie ma teraz dostępnych przedmiotów. Sprawdź nasze ogłoszenia OLX lub napisz, czego szukasz.</p></div>';
        $content .= salesActions($site).'</div></div></section>';
    } else {
        $matches = array_values(array_filter($products, fn(array $p): bool => $p['slug'] === $route));
        if (count($matches) !== 1) throw new \RuntimeException('not_found');
        $p = $matches[0]; $title = $p['name'].' | Lombard SEZAM Gorzów';
        $description = $p['name'].' — zobacz zdjęcia, cenę i dostępność w Lombardzie SEZAM przy Pocztowej 11 w Gorzowie.';
        $ogImage = $site['origin'].$p['image'];
        $crumbs .= '<a href="/na-sprzedaz/'.html($p['category']).'/">'.html(CATEGORIES[$p['category']]).'</a><span aria-hidden="true">/</span><span aria-current="page">Przedmiot</span></nav>';
        $gallery = '<div class="sales-gallery"><a class="sales-main-image" href="'.html($p['image']).'" target="_blank" rel="noopener noreferrer"><img src="'.html($p['image']).'" alt="'.html($p['name']).'" width="900" height="900" fetchpriority="high"></a>';
        if (count($p['images']) > 1) {
            $gallery .= '<div class="sales-thumbnails" aria-label="Wszystkie zdjęcia przedmiotu">';
            foreach ($p['images'] as $i => $image) $gallery .= '<a href="'.html($image).'"'.($i === 0 ? ' aria-current="true"' : '').' aria-label="Zdjęcie '.($i+1).' — '.html($p['name']).'" target="_blank" rel="noopener noreferrer"><img src="'.html($image).'" alt="'.html($p['name']).' — zdjęcie '.($i+1).'" loading="lazy" decoding="async" width="180" height="180"></a>';
            $gallery .= '</div>';
        }
        $gallery .= '</div>';
        $content = '<section class="section wrap sales-section"><div class="sales-product-heading"><span class="eyebrow muted">'.html(CATEGORIES[$p['category']]).'</span><h1>'.html($p['name']).'</h1></div><div class="sales-product">'.$gallery.'<div class="sales-product-details"><strong>'.priceLabel($p['price']).'</strong><p class="sales-status">'.statusLabel($p).'</p><div class="sales-product-description">'.html($p['description']).'</div><p class="sales-location">Odbiór: '.html($site['name']).', '.html($site['address']).'.</p><p class="sales-date">Cena z ogłoszenia OLX, dane z dnia '.html($p['checked_on']).'. Potwierdź aktualną cenę i dostępność.</p>';
        if (available($p)) $content .= '<div class="sales-actions"><a class="btn btn-dark" href="'.html($p['source_url']).'" target="_blank" rel="noopener noreferrer">Zobacz ogłoszenie na OLX <span aria-hidden="true">↗</span></a></div>';
        else $content .= '<div class="sales-unavailable"><strong>Ta oferta jest już niedostępna.</strong> <a href="/na-sprzedaz/">Zobacz aktualne przedmioty</a>.</div>';
        $inquiry = rawurlencode('Dzień dobry, pytam o: '.$p['name'].' '.$canonical);
        $content .= '<div class="sales-actions"><a class="text-link" href="https://wa.me/'.html($site['whatsapp']).'?text='.html($inquiry).'" target="_blank" rel="noopener noreferrer">Zapytaj o ten przedmiot na WhatsApp <span aria-hidden="true">→</span></a></div></div></div></section>';
        $data = ['@context'=>'https://schema.org','@type'=>'Product','name'=>$p['name'],'description'=>$p['description'],'image'=>array_map(fn(string $i): string => $site['origin'].$i,$p['images']),'sku'=>$p['source_id'],'offers'=>['@type'=>'Offer','url'=>$canonical,'priceCurrency'=>'PLN','price'=>(string)$p['price'],'availability'=>'https://schema.org/'.($p['status']==='in_stock'?'InStock':'OutOfStock'),'seller'=>['@type'=>'Store','name'=>$site['name'],'url'=>$site['origin'].'/']]];
        if (!empty($p['price_valid_until'])) $data['offers']['priceValidUntil'] = $p['price_valid_until'];
        $schema = '<script type="application/ld+json">'.json_encode($data,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE|JSON_HEX_TAG|JSON_HEX_AMP|JSON_HEX_APOS|JSON_HEX_QUOT).'</script>';
    }
    $page = preg_replace_callback('~<main id="main">.*?</main>~s',fn() => '<main id="main">'.$crumbs.$content.$schema.'</main>',$template,1,$changed);
    if ($changed !== 1) throw new \RuntimeException('template_invalid');
    $page = preg_replace_callback('~<title>.*?</title>~s',fn() => '<title>'.html($title).'</title>',$page,1);
    $page = preg_replace_callback('~<meta name="description"[^>]*>~',fn() => '<meta name="description" content="'.html($description).'">',$page,1);
    $page = preg_replace_callback('~<link rel="canonical"[^>]*>~',fn() => '<link rel="canonical" href="'.html($canonical).'">',$page,1);
    // The public template itself is noindex. Only the final production routes are indexable.
    $page = preg_replace('~<meta\s+name="robots"[^>]*>~i','',$page);
    $page = preg_replace('~<!-- SEZAM_SALES_(?:PLACEHOLDER|TEMPLATE_V1) -->~','',$page);
    $page = preg_replace('~<meta\s+property="og:(?:title|description|url|image)"[^>]*>~i','',$page);
    $social = '<meta property="og:title" content="'.html($title).'"><meta property="og:description" content="'.html($description).'"><meta property="og:url" content="'.html($canonical).'">';
    if ($ogImage !== null) $social .= '<meta property="og:image" content="'.html($ogImage).'">';
    if (!str_contains($page,'href="/sales.css"')) $social .= '<link rel="stylesheet" href="/sales.css">';
    if (!str_contains($page,'src="/sales.js"')) $social .= '<script src="/sales.js" defer></script>';
    $host = strtolower(explode(':',$_SERVER['HTTP_HOST'] ?? 'lombardgorzow.com')[0]);
    if (!in_array($host,['lombardgorzow.com','www.lombardgorzow.com'],true)) $social .= '<meta name="robots" content="noindex,follow">';
    $page = str_replace('</head>',$social.'</head>',$page);
    return str_replace('Grafiki aranżacyjne.','Zdjęcia oferowanych przedmiotów.',$page);
}
function renderSitemap(App $app, array $snapshot): string {
    validateProducts($app, $snapshot['products']); $site = siteMetadata($app);
    $paths = ['/na-sprzedaz/'];
    foreach (array_keys(CATEGORIES) as $category) $paths[] = '/na-sprzedaz/'.$category.'/';
    foreach ($snapshot['products'] as $p) $paths[] = productPath($p);
    $out = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">';
    foreach (array_unique($paths) as $path) $out .= '<url><loc>'.html($site['origin'].$path).'</loc></url>';
    return $out.'</urlset>';
}
