import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
const root=process.env.TEST_URL||'http://127.0.0.1:4173/';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox'],headless:true});
const p=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const errors=[];p.on('pageerror',e=>errors.push(e.message));
const go=async path=>{const r=await p.goto(new URL(path,root).href,{waitUntil:'networkidle'});assert.equal(r.status(),200,path);};
const text=async s=>(await p.locator(s).innerText()).replace(/\s/g,'');
const screenshot=async name=>{await p.locator('img[src]').evaluateAll(imgs=>Promise.all(imgs.map(i=>{i.loading='eager';return i.decode();})));await p.screenshot({path:`/tmp/sezam-v3-${name}.png`,fullPage:true});};
try{
 for(const route of['','gotowka/','skup-zlota/','telefony-laptopy/','serwis-gsm/','czesci/','na-sprzedaz/','o-nas/','kontakt/','pytania/','galeria/','blog/']){
  await go(route);assert.equal(await p.locator('h1').count(),1);
  await p.locator('img[src]').evaluateAll(imgs=>Promise.all(imgs.map(i=>{i.loading='eager';return i.decode();})));
  assert.deepEqual(await p.locator('img[src]').evaluateAll(imgs=>imgs.filter(i=>!i.naturalWidth).map(i=>i.src)),[]);
  assert.deepEqual(await p.locator('a[href^="#"]').evaluateAll(as=>as.filter(a=>a.hash&&!document.getElementById(a.hash.slice(1))).map(a=>a.hash)),[]);
  for(const width of[320,390,768,1440]){await p.setViewportSize({width,height:900});await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,`Overflow ${route} ${width}`);}
  if(['','gotowka/','skup-zlota/','kontakt/'].includes(route))await screenshot(route.replace('/','')||'home');
 }
 await go('');
 await p.getByRole('button',{name:'Telefony',exact:true}).click();
 assert.match(await p.locator('#showcase-image').getAttribute('src'),/phones.webp$/);
 assert.equal(await p.getByRole('button',{name:'Telefony',exact:true}).getAttribute('aria-pressed'),'true');
 await p.getByRole('button',{name:'Laptopy',exact:true}).click();
 assert.match(await p.locator('#showcase-image').getAttribute('src'),/laptop.webp$/);
 await go('na-sprzedaz/');
 await p.getByRole('button',{name:'Telefony',exact:true}).click();
 assert.equal(await p.locator('.sale-item:visible').count(),1);
 assert.match(await p.locator('.sale-item:visible').innerText(),/Twój następny telefon/);
 await p.getByRole('button',{name:'Wszystko',exact:true}).click();
 assert.equal(await p.locator('.sale-item:visible').count(),3);
 await p.emulateMedia({reducedMotion:'no-preference'});
 await go('');
 await p.locator('.service-card').first().scrollIntoViewIfNeeded();
 await p.waitForFunction(()=>getComputedStyle(document.querySelector('.service-card')).opacity==='1');
 assert.equal(await p.locator('.service-card').first().isVisible(),true);
 await p.emulateMedia({reducedMotion:'reduce'});
 await go('gotowka/');assert.equal(await text('#fee'),'25,00zł');assert.equal(await text('#total'),'1025,00zł');await p.locator('[name="period"][value="30"]').check();assert.equal(await text('#total'),'1050,00zł');await p.locator('[data-amount="5000"]').click();assert.equal(await text('#total'),'5250,00zł');await p.locator('#amount').fill('');assert.equal(await p.locator('#amount-error').isVisible(),true);assert.equal(await text('#total'),'—');await p.locator('#amount').fill('50001');assert.equal(await p.locator('#amount').getAttribute('aria-invalid'),'true');await p.locator('#amount').fill('100');assert.equal(await text('#total'),'105,00zł');await p.locator('#amount-range').fill('50000');assert.equal(await text('#total'),'52500,00zł');
 await go('skup-zlota/');await p.getByRole('tab',{name:'Srebro',exact:true}).click();assert.equal(await text('#price-rows tr:last-child td'),'4,15zł/g');await p.locator('#weight-tier').selectOption('0');assert.equal(await text('#price-rows tr:last-child td'),'3,99zł/g');await p.getByRole('tab',{name:'Srebro',exact:true}).press('ArrowLeft');assert.equal(await p.locator('#tab-gold').getAttribute('aria-selected'),'true');assert.equal(await text('#price-rows tr:nth-child(3) td'),'264,30zł/g');
 await go('pytania/');await p.locator('.questions summary').first().click();assert.equal(await p.locator('.questions details').first().getAttribute('open'),'');
 await go('galeria/');await p.locator('.gallery-photo').first().click();assert.equal(await p.getByRole('dialog').isVisible(),true);await p.keyboard.press('Escape');assert.equal(await p.getByRole('dialog').isVisible(),false);
 await go('blog/');await p.locator('.article-details summary').first().click();assert.equal(await p.locator('.article-body').first().isVisible(),true);
 await p.setViewportSize({width:390,height:844});await go('');await p.getByRole('button',{name:'Menu'}).click();assert.equal(await p.locator('#site-nav').isVisible(),true);await p.locator('#site-nav').getByRole('link',{name:'Kontakt',exact:true}).click();assert.match(p.url(),/kontakt\/$/);await go('');await screenshot('mobile');
 assert.deepEqual(errors,[]);console.log('PASS: 12 pages, images, anchors, 48 viewport checks, calculator boundaries, prices and weight tiers, keyboard tabs, FAQ, gallery lightbox, articles, mobile navigation, hero categories, sale filters, scroll animation and reduced-motion mode.');
}finally{await browser.close();}
