import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
const root=process.env.TEST_URL||'http://127.0.0.1:4174/lombardgorzow/';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
const p=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
const errors=[];p.on('pageerror',e=>errors.push(e.message));
const go=async path=>{const r=await p.goto(new URL(path,root).href,{waitUntil:'networkidle'});assert.equal(r.status(),200,path);};
try{
 for(const route of['wersje/','wersja-1/','wersja-2/','wersja-3/','wersja-4/','wersja-5/','impuls-wersje/','wersja-6/','wersja-7/','wersja-8/','wersja-9/','wersja-10/']){
  await go(route);assert.equal(await p.locator('main h1').count(),1,route);assert.equal(await p.locator('main').isVisible(),true);
  await p.locator('img[src]').evaluateAll(imgs=>Promise.all(imgs.map(i=>i.decode())));
  for(const width of[320,390,768,1440]){
   await p.setViewportSize({width,height:1000});await p.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   const overflow=await p.evaluate(()=>({w:innerWidth,scroll:document.documentElement.scrollWidth,els:[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+2&&!e.closest('.preview-window')).map(e=>e.className).slice(0,12)}));
   assert.equal(overflow.scroll<=overflow.w,true,route+' '+width+' '+JSON.stringify(overflow));
  }
  await p.screenshot({path:'/tmp/sezam-'+route.replace('/','')+'.png',fullPage:true});
  if(!['wersje/','impuls-wersje/'].includes(route)){
   assert.equal(await p.locator('.comparison-toolbar a[aria-current="page"]').count(),1);
   await p.locator('.v-header nav').getByRole('link',{name:'Gotówka',exact:true}).click();assert.match(p.url(),/gotowka\/$/);
  }
 }
 await go('impuls-wersje/');assert.equal(await p.locator('.concept-card').count(),5);assert.equal(await p.locator('.concept-preview iframe').count(),5);await p.locator('.concept-description').first().getByRole('link',{name:'Otwórz pełną wersję'}).click();assert.match(p.url(),/wersja-6\/$/);await p.locator('.comparison-toolbar').getByRole('link',{name:'Wersja 10: Impuls Plakat',exact:true}).click();assert.match(p.url(),/wersja-10\/$/);
 await go('wersje/');assert.equal(await p.locator('.concept-card').count(),5);assert.equal(await p.locator('.concept-preview iframe').count(),5);
 await p.locator('.concept-description').first().getByRole('link',{name:'Otwórz pełną wersję'}).click();assert.match(p.url(),/wersja-1\/$/);
 await p.locator('.comparison-toolbar').getByRole('link',{name:'Wersja 2: Impuls',exact:true}).click();assert.match(p.url(),/wersja-2\/$/);
 await go('wersja-3/');const result=async()=>(await p.locator('#variant-cost').innerText()).replace(/\s/g,'');assert.equal(await result(),'50,00zł');await p.locator('#variant-period').selectOption('15');assert.equal(await result(),'25,00zł');await p.locator('#variant-amount').fill('2000');assert.equal(await result(),'50,00zł');await p.locator('#variant-amount').fill('');assert.equal(await result(),'—');assert.equal(await p.locator('#variant-error').isVisible(),true);await p.locator('#variant-amount').fill('50001');assert.equal(await result(),'—');
 await go('wersja-5/');await p.locator('.forma-accordion summary').nth(1).click();assert.equal(await p.locator('.forma-accordion details').nth(1).getAttribute('open'),'');
 await p.setViewportSize({width:390,height:844});await go('wersja-1/');await p.screenshot({path:'/tmp/sezam-variant-mobile.png',fullPage:true});
 await go('wersja-1/?preview=1');assert.equal(await p.locator('.comparison-toolbar').isVisible(),false);
 await go('');assert.equal(await p.locator('main>section').count(),2);assert.equal(await p.locator('.original-logo').count(),2);
 assert.deepEqual(errors,[]);console.log('PASS: 10 independent homepages, 2 comparison hubs, 48 viewport checks, images, service navigation, concept switching, fee widget, accordion, previews and original homepage unchanged.');
}finally{await browser.close();}
