import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import {mkdir} from 'node:fs/promises';
const root=process.env.TEST_URL||'http://127.0.0.1:4174/lombardgorzow/';
const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const p=await b.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
await p.context().grantPermissions(['clipboard-read','clipboard-write']);
const errors=[];p.on('pageerror',e=>errors.push(e.message));
const go=async r=>{const response=await p.goto(new URL(r,root).href,{waitUntil:'networkidle'});assert.equal(response.status(),200,r);await p.evaluate(()=>document.fonts.ready);};
try{
 await mkdir('public/previews',{recursive:true});
 for(const n of [21,22,23,24,25]){
  await go(`wersja-${n}/`);assert.equal(await p.locator('main h1').count(),1);
  await p.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode())));
  for(const width of [320,390,768,1440]){
   await p.setViewportSize({width,height:1000});await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${n} ${width}`);
   if(width===1440||width===390)await p.screenshot({path:`/tmp/sezam-lab-${n}-${width}.png`,fullPage:true});
  }
  for(const path of ['gotowka','skup-zlota','na-sprzedaz','serwis-gsm'])assert.ok(await p.locator(`main a[href="${new URL(path+'/',root).pathname}"]`).count(),`${n} ${path}`);
  assert.equal(await p.locator('.lab-compare [aria-current]').textContent().then(t=>t.slice(0,2)),String(n));
  await p.locator('.lab-compare').evaluate(e=>e.hidden=true);await p.screenshot({path:`public/previews/lab-${n}.jpg`,type:'jpeg',quality:85});await p.locator('.lab-compare').evaluate(e=>e.hidden=false);
  await p.setViewportSize({width:390,height:844});await p.getByRole('button',{name:'Menu',exact:true}).click();assert.equal(await p.locator('#lab-nav').isVisible(),true);await p.keyboard.press('Escape');assert.equal(await p.locator('#lab-nav').isVisible(),false);
  await p.getByRole('button',{name:'Menu',exact:true}).click();await p.locator('#lab-nav').getByRole('link',{name:'Gotówka',exact:true}).click();assert.match(p.url(),/gotowka\/$/);
 }
 await go('wersja-21/');for(const s of ['cash','sell','buy','repair']){await p.locator('#visit-purpose').selectOption(s);assert.equal(await p.locator('#guide-result li').count(),3);assert.ok(await p.locator('#guide-result .lab-button').getAttribute('href'));}await p.locator('.lab-copy').click();await expect(p.locator('.copy-status')).toHaveText('Lista skopiowana.');assert.match(await p.evaluate(()=>navigator.clipboard.readText()),/Naprawa telefonu/);
 await go('wersja-22/');for(const [i,t] of ['Złoto i biżuteria','Telefon','Laptop'].entries()){await p.locator('[data-object]').nth(i).click();assert.equal(await p.locator('#object-title').textContent(),t);assert.equal(await p.locator('#object-actions a').count(),3);await p.locator('.labx-objects-image').evaluate(i=>i.decode());}await p.locator('[data-object]').nth(1).click();await p.locator('#object-actions a').last().click();assert.match(p.url(),/serwis-gsm\/$/);
 await go('wersja-23/');await p.locator('#lab-amount').fill('2000');assert.match(await p.locator('#lab-fee').textContent(),/100/);assert.match(await p.locator('#lab-total').textContent(),/2\s*100/);await p.locator('[name="lab-period"][value="15"]').check();assert.match(await p.locator('#lab-fee').textContent(),/50/);for(const value of ['','0','-1','50001']){await p.locator('#lab-amount').fill(value);assert.equal(await p.locator('#lab-amount').getAttribute('aria-invalid'),'true');assert.equal(await p.locator('#lab-fee').textContent(),'—');}await p.locator('#lab-amount').fill('1000.50');assert.equal(await p.locator('#lab-amount').getAttribute('aria-invalid'),'false');
 await go('wersja-24/');await p.locator('#visit-day').selectOption('sunday');assert.match(await p.locator('#visit-result').textContent(),/zamknięty/);await p.locator('#visit-day').selectOption('saturday');assert.match(await p.locator('#visit-result').textContent(),/14:00/);for(const t of ['walk','drive','transit']){await p.locator('#visit-transport').selectOption(t);assert.ok(await p.locator('#visit-result a').first().getAttribute('href'));}
 await go('wersja-25/');for(const [i,t] of ['Ekran','Bateria','Ładowanie','Inny problem'].entries()){await p.locator('[data-issue]').nth(i).click();assert.equal(await p.locator('#labx-repair-result h3').textContent(),t);assert.equal(await p.locator('[aria-pressed=true]').count(),1);}await p.locator('[data-issue]').first().focus();await p.keyboard.press('Tab');await p.keyboard.press('Enter');assert.equal(await p.locator('[data-issue]').nth(1).getAttribute('aria-pressed'),'true');
 assert.deepEqual(errors,[]);console.log('PASS: 5 pages, 20 viewports, all images, navigation, mobile menus, keyboard, 5 interactive tools, calculator boundaries.');
}finally{await b.close();}
