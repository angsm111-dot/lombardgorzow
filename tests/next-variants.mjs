import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
const root=process.env.TEST_URL||'http://127.0.0.1:4174/lombardgorzow/';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const p=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const errors=[];p.on('pageerror',e=>errors.push(e.message));
const go=async route=>{const r=await p.goto(new URL(route,root).href,{waitUntil:'networkidle'});assert.equal(r.status(),200,route);};
try{
 for(const route of ['swieze-wersje/',...Array.from({length:5},(_,i)=>`wersja-${16+i}/`)]){
  await go(route);assert.equal(await p.locator('main h1').count(),1);await p.locator('img').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode())));
  for(const width of [320,390,768,1440]){
   await p.setViewportSize({width,height:1000});await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,route+' overflow at '+width);
   if(width===390||width===1440)await p.screenshot({path:`/tmp/sezam-next-${route.replace('/','')}-${width}.png`,fullPage:true});
  }
  if(route!=='swieze-wersje/'){
   assert.equal(await p.locator('.nx-compare [aria-current]').count(),1);
   for(const path of (route==='wersja-17/'?['gotowka']:['gotowka','skup-zlota','na-sprzedaz','serwis-gsm']))assert.ok(await p.locator(`main a[href="${new URL(path+'/',root).pathname}"]`).count(),route+' '+path);
   await p.setViewportSize({width:390,height:844});await p.getByRole('button',{name:'Menu'}).click();assert.equal(await p.locator('#nx-nav').isVisible(),true);await p.keyboard.press('Escape');assert.equal(await p.locator('#nx-nav').isVisible(),false);
   await p.getByRole('button',{name:'Menu'}).click();await p.locator('#nx-nav').getByRole('link',{name:'Gotówka',exact:true}).click();assert.match(p.url(),/gotowka\/$/);
  }
 }
 await go('wersja-17/');
 for(const [i,path] of ['gotowka','skup-zlota','na-sprzedaz','serwis-gsm'].entries()){
  const b=p.locator('[data-next-intent]').nth(i);await b.click();assert.equal(await b.getAttribute('aria-pressed'),'true');assert.equal(await p.locator('#nx-intent-link').getAttribute('href'),new URL(path+'/',root).pathname);await p.locator('#nx-intent-image').evaluate(i=>i.decode());
 }
 await go('wersja-18/');for(const row of await p.locator('.konk-index details').all()){if(await row.getAttribute('open')===null)await row.locator('summary').click();assert.equal(await row.locator('.konk-detail').isVisible(),true);}
 await go('swieze-wersje/');assert.equal(await p.locator('.nx-projects article').count(),5);await p.locator('.nx-projects .nx-button').first().click();assert.match(p.url(),/wersja-16\/$/);
 await go('wersja-16/?preview=1');assert.equal(await p.locator('.nx-compare').isVisible(),false);
 await go('');assert.equal(await p.locator('main>section').count(),2);assert.equal(await p.locator('.original-logo').count(),2);
 assert.deepEqual(errors,[]);console.log('PASS: 5 new concepts, comparison hub, 24 viewport checks, 4 intent states, mobile menu and Escape, service links, accordion, images and original homepage.');
}finally{await browser.close();}
