#!/usr/bin/env python3
"""Publish only the approved Christmas article, first blog card and sitemap URL."""
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import posixpath
import re
import stat
import sys
import urllib.request
import xml.etree.ElementTree as ET

ORIGIN = 'https://lombardgorzow.com'
ROUTE = '/blog/bizuteria-prezent-styl-boze-narodzenie-2026/'
ARTICLE = ROUTE.strip('/') + '/index.html'
ALLOWED = {ARTICLE, 'blog/index.html', 'sitemap.xml'}
ROOT = '/home/vvictgzv'
PUBLIC = ROOT + '/public_html'
PRIVATE = ROOT + '/private'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def replace_one(pattern, replacement, text, flags=0):
    result, count = re.subn(pattern, lambda _: replacement, text, flags=flags)
    if count != 1:
        raise ValueError('Expected one HTML marker')
    return result

def validate_payload(p):
    if p['schema'] != 1 or p['origin'] != ORIGIN or p['route'] != ROUTE:
        raise ValueError('Unexpected article identity')
    if not re.fullmatch('[a-f0-9]{40}', p['source_commit']):
        raise ValueError('Source commit is not pinned')
    if p['image'] != '/assets/accepted-jewelry.webp':
        raise ValueError('Unexpected image')
    if p['main_html'].count('<h1>') != 1 or p['main_html'].count('Lombard Gorzów') < 1 or 'lombard w Gorzowie' not in p['main_html']:
        raise ValueError('Article content is incomplete')
    if '<form' in p['main_html'].lower() or 'mailto:' in p['main_html'].lower():
        raise ValueError('Unexpected contact method')
    if '2026-11-28' not in p['main_html'] or ROUTE not in p['card_html']:
        raise ValueError('Article date or card identity differs')
    if p['card_html'].count('<article class="journal-card">') != 1:
        raise ValueError('Expected a single blog card')

def prepare(p, blog_bytes, sitemap_bytes):
    validate_payload(p)
    blog = blog_bytes.decode('utf-8')
    if blog.count('<main id="main">') != 1 or blog.count('<div class="journal-grid">') != 1:
        raise ValueError('The current blog has an unexpected layout')
    if '/assets/' not in blog or 'tel:+48601775146' not in blog:
        raise ValueError('The current blog has an unexpected site identity')
    if ROUTE in blog:
        if p['card_html'] not in blog:
            raise ValueError('A different card already uses the article route')
        blog_after = blog
    else:
        blog_after = blog.replace('<div class="journal-grid">', '<div class="journal-grid">' + p['card_html'], 1)
    article = replace_one(r'<main id="main">.*?</main>', '<main id="main">\n' + p['main_html'] + '\n</main>', blog, re.S)
    article = replace_one(r'<title>.*?</title>', '<title>' + html.escape(p['title']) + '</title>', article, re.S)
    for key, value in [('description',p['description']), ('og:type','article'), ('og:title',p['title']), ('og:description',p['description']), ('og:url',ORIGIN+ROUTE), ('og:image',ORIGIN+p['image'])]:
        attribute = 'property' if key.startswith('og:') else 'name'
        pattern = r'<meta\b(?=[^>]*\b' + attribute + r'="' + re.escape(key) + r'")[^>]*>'
        article = replace_one(pattern, '<meta '+attribute+'="'+key+'" content="'+html.escape(value,quote=True)+'">', article)
    article = replace_one(r'<link\b(?=[^>]*\brel="canonical")[^>]*>', '<link rel="canonical" href="'+ORIGIN+ROUTE+'">', article)
    article = replace_one(r'<body\b[^>]*>', '<body class="page-subpage page-blog-swieta-styl">', article)
    if re.search(r'<meta\b[^>]*\bname="(?:robots|googlebot)"[^>]*\bcontent="[^"]*noindex',article,re.I):
        raise ValueError('The current blog is not indexed as production')
    if article.count('<h1>') != 1:
        raise ValueError('Expected one article heading')
    tree = ET.fromstring(sitemap_bytes)
    namespace = '{http://www.sitemaps.org/schemas/sitemap/0.9}'
    urls = [el.text for el in tree.findall(namespace+'url/'+namespace+'loc')]
    sitemap = sitemap_bytes.decode('utf-8')
    if not urls or any(not x.startswith(ORIGIN+'/') for x in urls):
        raise ValueError('Unexpected production sitemap origin')
    if ORIGIN+ROUTE not in urls:
        sitemap = replace_one(r'</urlset>', '  <url><loc>'+ORIGIN+ROUTE+'</loc><lastmod>2026-11-28</lastmod></url>\n</urlset>', sitemap)
    ET.fromstring(sitemap)
    return {ARTICLE:article.encode('utf-8'), 'blog/index.html':blog_after.encode('utf-8'), 'sitemap.xml':sitemap.encode('utf-8')}

def read(sftp,path,limit=5000000):
    a=sftp.lstat(path)
    if not stat.S_ISREG(a.st_mode) or a.st_size>limit:
        raise ValueError('Unexpected remote file type or size')
    with sftp.open(path,'rb') as f:
        return f.read()

def absent(sftp,path):
    try:
        sftp.lstat(path)
        return False
    except FileNotFoundError:
        return True

def directory(sftp,path):
    if not stat.S_ISDIR(sftp.lstat(path).st_mode):
        raise ValueError('Unexpected remote directory')

def write(sftp,path,data,mode=0o600):
    if not absent(sftp,path):
        raise ValueError('Staging path already exists')
    with sftp.open(path,'xb') as f:
        f.write(data)
    sftp.chmod(path,mode)
    if read(sftp,path)!=data:
        raise ValueError('Staging checksum differs')

def publish(p):
    import paramiko
    if not os.environ.get('JDM_PASSWORD'):
        raise RuntimeError('JDM_PASSWORD is not configured')
    run=os.environ['GITHUB_RUN_ID']+'-'+os.environ.get('GITHUB_RUN_ATTEMPT','1')
    if not re.fullmatch(r'[0-9]+-[0-9]+',run):
        raise ValueError('Unexpected run identity')
    client=paramiko.SSHClient()
    client.load_host_keys('deploy/jdm_known_hosts_web13')
    client.set_missing_host_key_policy(paramiko.RejectPolicy())
    client.connect('web13.jdm.pl',port=2233,username='vvictgzv',password=os.environ['JDM_PASSWORD'],look_for_keys=False,allow_agent=False,timeout=20,banner_timeout=20,auth_timeout=20)
    sftp=client.open_sftp()
    lock_in=lock_out=lock_err=None
    changed=[]
    originals={}
    stage=PRIVATE+'/christmas-blog-2026-'+run
    try:
        for path in [ROOT,PUBLIC,PRIVATE,PUBLIC+'/blog',ROOT+'/.sezam-nowa-deploy']:
            directory(sftp,path)
        lock_in,lock_out,lock_err=client.exec_command("flock -n /home/vvictgzv/.sezam-nowa-deploy/deployment.lock sh -c 'echo SEZAM_BLOG_LOCKED; cat >/dev/null'",timeout=20)
        if lock_out.readline().strip()!='SEZAM_BLOG_LOCKED':
            raise RuntimeError('Deployment is busy')
        if digest(read(sftp,PUBLIC+p['image']))!=p['image_sha256']:
            raise ValueError('Existing production image checksum differs')
        originals['blog/index.html']=read(sftp,PUBLIC+'/blog/index.html')
        originals['sitemap.xml']=read(sftp,PUBLIC+'/sitemap.xml')
        prepared=prepare(p,originals['blog/index.html'],originals['sitemap.xml'])
        assert set(prepared)==ALLOWED
        target_dir=PUBLIC+ROUTE.rstrip('/')
        if not absent(sftp,target_dir):
            directory(sftp,target_dir)
        if not absent(sftp,PUBLIC+'/'+ARTICLE):
            old=read(sftp,PUBLIC+'/'+ARTICLE)
            if old!=prepared[ARTICLE]:
                raise ValueError('Article route already has a different page')
            originals[ARTICLE]=old
        else:
            originals[ARTICLE]=None
        if not absent(sftp,stage):
            raise ValueError('Private backup path already exists')
        sftp.mkdir(stage,0o700)
        for i,(name,data) in enumerate(prepared.items()):
            write(sftp,stage+'/new-'+str(i),data,0o644)
            if originals[name] is not None:
                write(sftp,stage+'/before-'+str(i),originals[name])
        report={'schema':1,'origin':ORIGIN,'route':ROUTE,'source_commit':p['source_commit'],'deploy_commit':os.environ.get('GITHUB_SHA'),'run':run,'targets':{name:{'before_sha256':digest(originals[name]) if originals[name] is not None else None,'after_sha256':digest(data)} for name,data in prepared.items()},'backup_directory':stage}
        write(sftp,stage+'/manifest.json',json.dumps(report,ensure_ascii=False,indent=2).encode())
        if absent(sftp,target_dir):
            sftp.mkdir(target_dir,0o755)
        for i,(name,data) in enumerate(prepared.items()):
            if originals[name]==data:
                continue
            sftp.posix_rename(stage+'/new-'+str(i),PUBLIC+'/'+name)
            changed.append(name)
        for name,data in prepared.items():
            if read(sftp,PUBLIC+'/'+name)!=data:
                raise ValueError('Published checksum differs')
        report['status']='succeeded'
        write(sftp,stage+'/result.json',json.dumps(report,ensure_ascii=False,indent=2).encode())
        Path('qa').mkdir(exist_ok=True)
        Path('qa/deployment.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
        Path('qa/article.html').write_bytes(prepared[ARTICLE])
        Path('qa/blog.html').write_bytes(prepared['blog/index.html'])
        print(json.dumps(report,ensure_ascii=False))
    except Exception:
        for i,name in enumerate(reversed(changed)):
            original=originals[name]
            if original is None:
                sftp.remove(PUBLIC+'/'+name)
            else:
                rollback=stage+'/rollback-'+str(i)
                write(sftp,rollback,original,0o644)
                sftp.posix_rename(rollback,PUBLIC+'/'+name)
        raise
    finally:
        if lock_in:
            lock_in.close()
        sftp.close()
        client.close()

def verify_http(p):
    url=ORIGIN+ROUTE
    request=urllib.request.Request(url,headers={'Cache-Control':'no-cache','User-Agent':'SEZAM-publication-check/1.0'})
    with urllib.request.urlopen(request,timeout=30) as response:
        if response.status!=200:
            raise RuntimeError('Article HTTP status is not 200')
        page=response.read().decode('utf-8')
    for expected in [p['headline'],'2026-11-28',p['image'],'lombard w Gorzowie',ORIGIN+ROUTE]:
        if expected not in page:
            raise ValueError('Public article content differs')
    with urllib.request.urlopen(ORIGIN+'/blog/',timeout=30) as response:
        blog=response.read().decode('utf-8')
    first=re.search(r'<article class="journal-card">(.*?)</article>',blog,re.S)
    if not first or ROUTE not in first[1]:
        raise ValueError('The new article is not the first blog card')
    with urllib.request.urlopen(ORIGIN+'/sitemap.xml',timeout=30) as response:
        sitemap=response.read().decode('utf-8')
    if ORIGIN+ROUTE not in sitemap:
        raise ValueError('Public sitemap is missing the article')
    print('Public HTTP check passed: article, newest card, sitemap')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    payload=json.loads(Path('deploy/christmas-2026.json').read_text())
    validate_payload(payload)
    if args.check:
        print('Approved article payload validated')
    else:
        publish(payload)
        verify_http(payload)
