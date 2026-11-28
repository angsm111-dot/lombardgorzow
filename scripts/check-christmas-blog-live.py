#!/usr/bin/env python3
"""Read-only browser checks of the published Christmas article and newest card."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ORIGIN='https://lombardgorzow.com'
ROUTE='/blog/bizuteria-prezent-styl-boze-narodzenie-2026/'
Path('qa').mkdir(exist_ok=True)
results=[]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('CHROME_BIN','/usr/bin/google-chrome'),args=['--no-sandbox'])
    for width in (1440,393):
        page=browser.new_page(viewport={'width':width,'height':1000 if width>1000 else 900},device_scale_factor=1)
        errors=[]
        page.on('pageerror',lambda error: errors.append(str(error)))
        response=page.goto(ORIGIN+ROUTE,wait_until='networkidle',timeout=60000)
        page.screenshot(path=f'qa/http-response-{width}.png')
        if response.status != 200:
            Path('qa/http-error.json').write_text(json.dumps({'url':ORIGIN+ROUTE,'status':response.status,'title':page.title(),'body':page.locator('body').inner_text()[:2000],'headers':{key:response.headers.get(key) for key in ('server','content-type','cf-mitigated')}},ensure_ascii=False,indent=2))
        assert response.status==200, response.status
        page.locator('h1').wait_for()
        assert page.locator('h1').count()==1
        assert 'Boże Narodzenie 2026' in page.locator('h1').inner_text()
        assert page.locator('.journal-article-header time').get_attribute('datetime')=='2026-11-28'
        assert page.locator('link[rel=canonical]').get_attribute('href')==ORIGIN+ROUTE
        assert page.locator('.journal-prose a strong').all_text_contents()==['Lombard Gorzów','lombard w Gorzowie']
        assert page.locator('.journal-prose p').count()>=12
        assert page.locator('.journal-article form, .journal-article a[href^="mailto:"]').count()==0
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
        photo=page.locator('.journal-cover img')
        assert photo.evaluate('(img)=>img.complete && img.naturalWidth===1672')
        page.screenshot(path=f'qa/article-{width}.png')
        photo.scroll_into_view_if_needed()
        page.screenshot(path=f'qa/article-photo-{width}.png')
        links=page.locator('.journal-prose a[href^="/"]').evaluate_all('(links)=>[...new Set(links.map(a=>a.getAttribute("href")))]')
        for link in links:
            result=page.request.get(ORIGIN+link)
            assert result.status==200, (link,result.status)
        response=page.goto(ORIGIN+'/blog/',wait_until='networkidle',timeout=60000)
        assert response.status==200
        first=page.locator('.journal-card').first
        assert first.locator('h2 a').get_attribute('href')==ROUTE
        assert first.locator('time').get_attribute('datetime')=='2026-11-28'
        assert first.locator('img').evaluate('(img)=>img.complete && img.naturalWidth===1672')
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 1')
        first.scroll_into_view_if_needed()
        page.screenshot(path=f'qa/blog-{width}.png')
        results.append({'width':width,'article_http':200,'first_card':ROUTE,'no_horizontal_overflow':True,'photo_loaded':True,'internal_article_links':len(links),'page_errors':errors})
        page.close()
    browser.close()
Path('qa/browser-checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False))
