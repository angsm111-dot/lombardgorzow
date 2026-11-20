#!/usr/bin/env python3
"""Build a reproducible, isolated staging export without changing Sites files."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITES_ORIGIN = 'https://sezam-nowa-wartosc-gorzow.angsm111.chatgpt.site'
JDM_ORIGIN = 'https://nowa.lombardgorzow.com'
OUTPUT = ROOT / 'output/jdm-nowa'
FROZEN_PREFIX = 'wersja-pierwotna/'


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


def validate(site, protected):
    check_frozen(site, protected)
    documents = {}
    for file in site.rglob('*.html'):
        documents[file.resolve()] = Document(file.read_text())
    problems = []

    def check_url(source, value):
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc:
            if not value.startswith(JDM_ORIGIN + '/'):
                return
        path = unquote(parsed.path)
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
            if robots != ['noindex,nofollow']:
                problems.append(f'{relative}: missing staging robots meta')
        for _, attrs in document.elements:
            for key in ('href', 'src', 'poster'):
                if attrs.get(key):
                    check_url(file, attrs[key])
        for raw in re.findall(r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, re.S):
            data = json.loads(raw)
            if data.get('@type') == 'BlogPosting':
                expected = JDM_ORIGIN + '/' + relative.removesuffix('index.html')
                if data.get('mainEntityOfPage', {}).get('@id') != expected:
                    problems.append(f'{relative}: BlogPosting page URL mismatch')
    for file in site.rglob('*.css'):
        for value in re.findall(r'url\(\s*["\']?([^"\')]+)', file.read_text()):
            check_url(file, value.strip())
    if (site / 'robots.txt').read_text() != 'User-agent: *\nDisallow: /\n':
        problems.append('robots.txt does not block staging crawling')
    sitemap = (site / 'sitemap.xml').read_text()
    if SITES_ORIGIN in sitemap or JDM_ORIGIN not in sitemap:
        problems.append('sitemap origin mismatch')
    if problems:
        raise ValueError('\n'.join(problems))
    return len(documents)


def main():
    protected = frozen_files()
    check_frozen(ROOT / 'dist', protected)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='build-', dir=OUTPUT) as temporary:
        build = Path(temporary)
        for name in ('scripts', 'src', 'config', 'dist'):
            shutil.copytree(ROOT / name, build / name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        subprocess.run([sys.executable, str(build / 'scripts/build-pages.py')], check=True)
        site = build / 'dist'
        for file in sorted(site.rglob('*')):
            if not file.is_file() or str(file.relative_to(site)).startswith(FROZEN_PREFIX):
                continue
            if file.suffix in ('.html', '.xml'):
                text = file.read_text().replace(SITES_ORIGIN, JDM_ORIGIN)
                if file.suffix == '.html':
                    text = re.sub(r'<meta\b(?=[^>]*\bname\s*=\s*["\']robots["\'])[^>]*>\s*', '', text, flags=re.I)
                    text, count = re.subn(r'<head\b[^>]*>', lambda m: m.group() + '\n<meta name="robots" content="noindex,nofollow">', text, count=1, flags=re.I)
                    if count != 1:
                        raise ValueError(f'Missing HTML head: {file.relative_to(site)}')
                file.write_text(text)
        (site / 'robots.txt').write_text('User-agent: *\nDisallow: /\n')
        pages = validate(site, protected)
        destination = OUTPUT / 'site'
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(site), destination)

    archive = OUTPUT / 'nowa-lombardgorzow-com.zip'
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
        'origin': JDM_ORIGIN, 'archive': str(archive), 'archive_sha256': digest(archive),
        'archive_bytes': archive.stat().st_size, 'files': len(files), 'html_pages': pages,
        'frozen_files_verified': len(protected), 'staging_noindex': True,
        'file_sha256': {str(p.relative_to(destination)): digest(p) for p in files},
    }
    (OUTPUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'file_sha256'}, indent=2))


if __name__ == '__main__':
    main()
