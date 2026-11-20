#!/usr/bin/env python3
"""Build a reproducible JDM preview or production export without changing sources."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITES_ORIGIN = 'https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site'
PREVIEW_ORIGIN = 'https://nowa.lombardgorzow.com'
PRODUCTION_ORIGIN = 'https://lombardgorzow.com'
TRANSFORM_REVISION = 'sezam-deploy-v3'
FROZEN_PREFIX = 'wersja-pierwotna/'
ROBOTS_META = r'<meta\b(?=[^>]*\bname\s*=\s*["\']robots["\'])[^>]*>\s*'


def deployment_profile(name='preview'):
    if name not in ('preview', 'production'):
        raise ValueError('Unknown deployment profile')
    origin = PRODUCTION_ORIGIN if name == 'production' else PREVIEW_ORIGIN
    fingerprint = hashlib.sha256(f'{TRANSFORM_REVISION}\n{name}\n{origin}'.encode()).hexdigest()
    return {'name': name, 'origin': origin, 'fingerprint': fingerprint}


def comparison_path(relative):
    return bool(re.match(r'^(?:wersja-[^/]+/|porownanie(?:-wersji)?/|odwazne/|kolejne/|koncepcje/)', relative)) or relative in ('404.html', 'assets/sales-template.html')


def catalog_payload_path(relative):
    return relative.startswith(('na-sprzedaz/', 'integracje/katalog/', 'assets/sales-feed-'))


def skip_catalog_source(relative, text, catalog_runtime):
    if not catalog_runtime or not catalog_payload_path(relative):
        return False
    if relative != 'na-sprzedaz/index.html' or '<!-- SEZAM_SALES_PLACEHOLDER -->' not in text:
        raise ValueError(f'Source archive collides with the active catalog runtime: {relative}')
    return True


def catalog_route(path):
    return bool(re.fullmatch(r'/na-sprzedaz(?:/[a-z0-9]+(?:-[a-z0-9]+)*)?/?', path)) or path in ('/integracje/katalog/oferty/', '/integracje/katalog/mapa/')


def static_path(relative):
    return (len(relative) <= 240 and all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]*', part) and part not in ('.', '..') for part in relative.split('/'))
            and not re.search(r'\.(?:php\d*|phtml|phar|cgi|pl|py|sh|bash|exe|dll)(?:\.|$)', relative, re.I)
            and Path(relative).suffix.lower().lstrip('.') in ('html', 'css', 'js', 'json', 'xml', 'txt', 'svg', 'webp', 'png', 'jpg', 'jpeg', 'gif', 'avif', 'ico', 'woff', 'woff2', 'ttf', 'otf', 'pdf', 'mp4', 'webm'))


def robots_text(profile, catalog_runtime=False):
    return ('User-agent: *\nDisallow: /\n' if profile['name'] == 'preview'
            else f'User-agent: *\nAllow: /\nSitemap: {profile["origin"]}/sitemap.xml\n'
                 + (f'Sitemap: {profile["origin"]}/integracje/katalog/mapa/\n' if catalog_runtime else ''))


def transform(relative, text, profile):
    if relative.startswith(FROZEN_PREFIX):
        return text
    if Path(relative).suffix in ('.html', '.xml', '.json'):
        origins = [SITES_ORIGIN, PREVIEW_ORIGIN, PRODUCTION_ORIGIN,
                   'https://www.lombardgorzow.com', 'https://www.nowa.lombardgorzow.com']
        replacements = {old: profile['origin'] for old in origins}
        replacements.update({old.replace('/', r'\/'): profile['origin'].replace('/', r'\/') for old in origins})
        text = re.sub('|'.join(re.escape(old) for old in sorted(replacements, key=len, reverse=True)),
                      lambda match: replacements[match.group()], text)
    if Path(relative).suffix == '.html':
        directives = []
        for tag in re.findall(ROBOTS_META, text, flags=re.I):
            match = re.search(r'\bcontent\s*=\s*(["\'])(.*?)\1', tag, flags=re.I)
            if match:
                directives.extend(value.strip().lower() for value in unescape(match[2]).split(',') if value.strip())
        text = re.sub(ROBOTS_META, '', text, flags=re.I)
        if profile['name'] == 'preview':
            directives = ['noindex', 'nofollow']
        elif comparison_path(relative):
            directives = [value for value in directives if value not in ('index', 'all')]
            if not {'noindex', 'none'}.intersection(directives):
                directives.append('noindex')
            if not {'follow', 'nofollow', 'none'}.intersection(directives):
                directives.append('follow')
        elif not directives:
            directives = ['index', 'follow']
        # Preserve deliberate source noindex/none outside comparison routes too.
        # Public sitemap validation rejects excluded pages instead of exposing them.
        robots = escape(','.join(dict.fromkeys(directives)), quote=True)
        text, count = re.subn(r'<head\b[^>]*>', lambda match: match.group() + f'\n<meta name="robots" content="{robots}">', text, count=1, flags=re.I)
        if count != 1:
            raise ValueError(f'Missing HTML head: {relative}')
    if SITES_ORIGIN in text or SITES_ORIGIN.replace('/', r'\/') in text:
        raise ValueError(f'Private Sites origin remains: {relative}')
    return text


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_files():
    manifest = json.loads((ROOT / 'config/frozen-versions.json').read_text())
    return {str(Path(name).relative_to('dist')): expected
            for version in manifest['versions']
            for name, expected in version['files'].items()}


def check_frozen(directory, protected):
    actual = {str(p.relative_to(directory))
              for p in (directory / 'wersja-pierwotna').rglob('*') if p.is_file()}
    if actual != set(protected):
        raise ValueError('Frozen version file inventory differs from its manifest.')
    for relative, expected in protected.items():
        if digest(directory / relative) != expected:
            raise ValueError(f'Frozen version changed: {relative}')


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


def validate(site, protected, profile, catalog_runtime=False):
    check_frozen(site, protected)
    documents = {}
    for file in site.rglob('*.html'):
        documents[file.resolve()] = Document(file.read_text())
    problems = []
    for file in site.rglob('*'):
        if file.is_file() and not static_path(str(file.relative_to(site))):
            problems.append(f'{file.relative_to(site)}: non-static or unsafe export path')

    def check_url(source, value):
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc:
            if not value.startswith(profile['origin'] + '/'):
                return
        path = unquote(parsed.path)
        if catalog_runtime and catalog_route(path):
            return
        target = ((site / path.lstrip('/')) if path.startswith('/')
                  else source.parent / path) if path else source
        target = target.resolve()
        if not target.is_relative_to(site.resolve()):
            problems.append(f'{source.relative_to(site)}: path escapes export: {value}')
            return
        if target.is_dir():
            target /= 'index.html'
        if not target.is_file():
            problems.append(f'{source.relative_to(site)}: missing local target: {value}')
        elif parsed.fragment and target in documents:
            ids = {attrs.get('id') for _, attrs in documents[target].elements}
            if unquote(parsed.fragment) not in ids:
                problems.append(f'{source.relative_to(site)}: missing anchor: {value}')

    for file, document in documents.items():
        text = file.read_text()
        relative = str(file.relative_to(site))
        if SITES_ORIGIN in text:
            problems.append(f'{relative}: private Sites origin remains')
        ids = Counter(a['id'] for _, a in document.elements if 'id' in a)
        if any(count > 1 for count in ids.values()):
            problems.append(f'{relative}: duplicate element IDs')
        if not relative.startswith(FROZEN_PREFIX):
            robots = [a.get('content', '') for t, a in document.elements
                      if t == 'meta' and a.get('name', '').lower() == 'robots']
            if len(robots) != 1:
                problems.append(f'{relative}: expected one robots meta')
            elif profile['name'] == 'preview' and robots != ['noindex,nofollow']:
                problems.append(f'{relative}: missing preview robots meta')
            elif profile['name'] == 'production':
                directives = {value.strip().lower() for value in robots[0].split(',')}
                should_exclude = comparison_path(relative)
                if should_exclude and not {'noindex', 'none'}.intersection(directives):
                    problems.append(f'{relative}: production indexing policy mismatch')
        for _, attrs in document.elements:
            for key in ('href', 'src', 'poster'):
                if attrs.get(key):
                    check_url(file, attrs[key])
        for raw in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.S):
            def nodes(value):
                if isinstance(value, dict):
                    yield value
                    for child in value.values():
                        yield from nodes(child)
                elif isinstance(value, list):
                    for child in value:
                        yield from nodes(child)
            for data in nodes(json.loads(raw)):
                kinds = data.get('@type', [])
                if kinds == 'BlogPosting' or isinstance(kinds, list) and 'BlogPosting' in kinds:
                    expected = profile['origin'] + '/' + relative.removesuffix('index.html')
                    page_id = data.get('mainEntityOfPage', {})
                    if (page_id.get('@id') if isinstance(page_id, dict) else page_id) != expected:
                        problems.append(f'{relative}: BlogPosting page URL mismatch')
    for file in site.rglob('*.css'):
        for value in re.findall(r'url\(\s*["\']?([^"\')]+)', file.read_text()):
            check_url(file, value.strip())
    if (site / 'robots.txt').read_text() != robots_text(profile, catalog_runtime):
        problems.append('robots.txt differs from deployment profile')
    sitemap = (site / 'sitemap.xml').read_text()
    if SITES_ORIGIN in sitemap or profile['origin'] not in sitemap:
        problems.append('sitemap origin mismatch')
    urls = re.findall(r'<loc>\s*([^<]+)\s*</loc>', sitemap, re.I)
    if not urls:
        problems.append('sitemap has no URLs')
    for raw in urls:
        url = unescape(raw.strip())
        if not url.startswith(profile['origin'] + '/'):
            problems.append(f'sitemap: unexpected origin: {url}')
            continue
        check_url(site / 'sitemap.xml', url)
        relative = urlsplit(url).path.lstrip('/')
        if not relative or relative.endswith('/'):
            relative += 'index.html'
        if profile['name'] == 'production' and comparison_path(relative):
            problems.append(f'sitemap: comparison page must be excluded: {url}')
        if profile['name'] == 'production':
            document = documents.get((site / relative).resolve())
            if document:
                for tag, attrs in document.elements:
                    if tag == 'meta' and attrs.get('name', '').lower() in ('robots', 'googlebot') and {'noindex', 'none'}.intersection(value.strip().lower() for value in attrs.get('content', '').split(',')):
                        problems.append(f'sitemap: intentionally excluded page must not be listed: {url}')
    if problems:
        raise ValueError('\n'.join(problems))
    return len(documents)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('preview', 'production'), default='preview')
    parser.add_argument('--catalog-runtime', action='store_true', help='Omit the managed listing placeholder when installing beside the approved live catalog.')
    args = parser.parse_args()
    profile = deployment_profile(args.profile)
    output = ROOT / ('output/jdm-production' if profile['name'] == 'production' else 'output/jdm-nowa')
    protected = frozen_files()
    check_frozen(ROOT / 'dist', protected)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='build-', dir=output) as temporary:
        build = Path(temporary)
        for name in ('scripts', 'src', 'config', 'dist'):
            shutil.copytree(ROOT / name, build / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        subprocess.run([sys.executable, str(build / 'scripts/build-pages.py')], check=True)
        site = build / 'dist'
        for file in sorted(site.rglob('*')):
            if not file.is_file() or str(file.relative_to(site)).startswith(FROZEN_PREFIX):
                continue
            relative = str(file.relative_to(site))
            if args.catalog_runtime and catalog_payload_path(relative) and skip_catalog_source(relative, file.read_text() if file.suffix == '.html' else '', True):
                file.unlink()
                continue
            if file.suffix in ('.html', '.xml', '.json'):
                file.write_text(transform(str(file.relative_to(site)), file.read_text(), profile))
        (site / 'robots.txt').write_text(robots_text(profile, args.catalog_runtime))
        pages = validate(site, protected, profile, args.catalog_runtime)
        destination = output / 'site'
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(site), destination)

    archive = output / ('lombardgorzow-com.zip' if profile['name'] == 'production' else 'nowa-lombardgorzow-com.zip')
    files = sorted(p for p in destination.rglob('*') if p.is_file())
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as package:
        for file in files:
            info = zipfile.ZipInfo(str(file.relative_to(destination)), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            package.writestr(info, file.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(archive) as package:
        if package.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
        for relative, expected in protected.items():
            if hashlib.sha256(package.read(relative)).hexdigest() != expected:
                raise ValueError(f'Frozen file changed in ZIP: {relative}')
    report = {
        'origin': profile['origin'], 'profile': profile['name'], 'profile_fingerprint': profile['fingerprint'], 'catalog_runtime': args.catalog_runtime,
        'archive': str(archive), 'archive_sha256': digest(archive),
        'archive_bytes': archive.stat().st_size, 'files': len(files), 'html_pages': pages,
        'frozen_files_verified': len(protected), 'staging_noindex': profile['name'] == 'preview',
        'file_sha256': {str(p.relative_to(destination)): digest(p) for p in files},
    }
    (output / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'file_sha256'}, indent=2))


if __name__ == '__main__':
    main()
