'use strict';
const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const money = n => new Intl.NumberFormat('pl-PL', {style:'currency',currency:'PLN'}).format(n);
const whatsapp = 'https://wa.me/48601775146';
const normalizePath = path => path.replace(/index\.html$/, '').replace(/\/+$/, '') || '/';
const pagePath = normalizePath(window.location.pathname);
const legacyPages = {'#oferta':'/oferta/', '#kalkulator':'/kalkulator/', '#o-nas':'/o-nas/', '#pytania':'/pytania/', '#kontakt':'/kontakt/'};
// The full homepage owns these anchors again; redirect only absent sections.
if (pagePath === '/' && Object.hasOwn(legacyPages, window.location.hash) && !document.getElementById(window.location.hash.slice(1))) {
  window.location.replace(legacyPages[window.location.hash] + window.location.search);
}
const offerings = {
  sell:{label:'MNIEJ RZECZY. WIĘCEJ MOŻLIWOŚCI.',title:'To, czego nie używasz,<br>może być wiele warte.',description:'Złota biżuteria, srebro, telefon czy laptop — przynieś je do SEZAM. Ocenimy przedmiot, przedstawimy propozycję i wypłacimy gotówkę po zaakceptowaniu warunków.',chips:['Złoto i srebro','Telefony','Laptopy','Monety i sztabki'],cta:'Sprawdź cennik złota',url:'/cennik-zlota/',inquiry:'Skup przedmiotu',image:'/assets/sezam-jewelry.webp',alt:'Złota biżuteria na jasnej kamiennej ekspozycji',caption:'Dobre rzeczy zasługują na nowy rozdział.'},
  loan:{label:'TWOJE RZECZY. TWOJE MOŻLIWOŚCI.',title:'Gotówka teraz.<br>Przedmiot odbierzesz później.',description:'Zastaw wartościowy przedmiot i uzyskaj pożyczkę. Przed podpisaniem umowy poznasz koszt oraz termin odbioru. Zacznij od kalkulatora, a szczegóły omówimy w punkcie.',chips:['Biżuteria','Złoto i srebro','Elektronika','Sprzęt techniczny'],cta:'Oblicz koszt pożyczki',url:'/kalkulator/',inquiry:'Pożyczka pod zastaw',image:'/assets/sezam-jewelry.webp',alt:'Złote obrączki i pierścionek na jasnej kamiennej ekspozycji',caption:'Wycena, jasne warunki i Twoja decyzja.'},
  buy:{label:'SPRAWDŹ. OBEJRZYJ. WYBIERZ.',title:'Wyjątkowe rzeczy.<br>Całkiem nowe historie.',description:'Odkryj biżuterię, telefony, laptopy i sprzęt dostępny w SEZAM. Na miejscu możesz przyjrzeć się wybranemu przedmiotowi, sprawdzić telefon i porozmawiać o szczegółach zakupu.',chips:['Biżuteria','Smartfony','Laptopy','Narzędzia i sprzęt'],cta:'Zobacz ofertę sprzedaży',url:'https://sezam.com.pl/oferta-olx-allegro/',inquiry:'Zakup biżuterii',image:'/assets/sezam-tech.webp',alt:'Smartfony i laptop na jasnym marmurowym podeście',caption:'Znajdź coś, co pasuje właśnie do Ciebie.'},
  repair:{label:'DRUGIE ŻYCIE TWOJEGO TELEFONU.',title:'Mała usterka?<br>Porozmawiajmy o naprawie.',description:'Uszkodzony wyświetlacz, zużyta bateria lub problem z ładowaniem? Serwis SEZAM zajmuje się naprawami telefonów. Podaj model i opisz usterkę — ustalimy możliwości oraz warunki naprawy.',chips:['Wyświetlacze','Baterie','Gniazda ładowania','Diagnostyka'],cta:'Zadzwoń do serwisu',url:'tel:+48601775146',inquiry:'Naprawa telefonu',image:'/assets/sezam-tech.webp',alt:'Telefon i laptop na jasnej marmurowej ekspozycji',caption:'Zanim wymienisz telefon, zapytaj o naprawę.'}
};
function selectOffer(key, focus=false, updateUrl=true){
  if (!$('#offer-panel') || !Object.hasOwn(offerings,key)) return;
  const o=offerings[key];
  $$('[data-tab]').forEach(b=>{const active=b.dataset.tab===key;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;if(active&&focus)b.focus()});
  $('#offer-panel').setAttribute('aria-labelledby','tab-'+key);$('#offer-panel').dataset.service=key;
  $('#offer-label').textContent=o.label;$('#offer-title').innerHTML=o.title;$('#offer-description').textContent=o.description;
  $('#offer-chips').replaceChildren(...o.chips.map(t=>{const e=document.createElement('span');e.textContent=t;return e}));
  const cta=$('#offer-cta');cta.replaceChildren(document.createTextNode(o.cta+' '));const arr=document.createElement('span');arr.innerHTML='<svg class="arrow-icon" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19 19 5M5 5h14v14"/></svg>';cta.append(arr);cta.href=o.url;
  if(o.url.startsWith('https:')){cta.target='_blank';cta.rel='noopener'}else{cta.removeAttribute('target');cta.removeAttribute('rel')}
  $('.offer-bottom button').dataset.inquiry=o.inquiry;
  const img=$('#offer-art img');img.src=o.image;img.alt=o.alt;
  $('#offer-art .art-bottom').firstChild.textContent=o.caption;
  $('.offer-detail').classList.remove('flash');void $('.offer-detail').offsetWidth;$('.offer-detail').classList.add('flash');
  if (updateUrl && pagePath === '/oferta') {
    const url = new URL(window.location.href);
    url.searchParams.set('usluga', key);
    window.history.replaceState(null, '', url);
  }
}
$$('[data-tab]').forEach(b=>{b.addEventListener('click',()=>selectOffer(b.dataset.tab));b.addEventListener('keydown',e=>{const tabs=$$('[data-tab]');let i=tabs.indexOf(b);if(e.key==='ArrowRight')i=(i+1)%tabs.length;else if(e.key==='ArrowLeft')i=(i+tabs.length-1)%tabs.length;else if(e.key==='Home')i=0;else if(e.key==='End')i=tabs.length-1;else return;e.preventDefault();selectOffer(tabs[i].dataset.tab,true)})});
if ($('#offer-panel')) {
  const restoreOffer = () => {
    const requested = new URLSearchParams(window.location.search).get('usluga');
    selectOffer(Object.hasOwn(offerings,requested) ? requested : 'sell', false, false);
  };
  restoreOffer();
  // Only the offer subpage stores its selected service in the query string.
  // Native homepage anchor navigation must not reset the selected tab.
  if (pagePath === '/oferta') window.addEventListener('popstate', restoreOffer);
}
// Homepage cards select the matching offer before the native anchor scroll.
// Navigation and service links on other pages remain ordinary page links.
$$('.quick-links a[data-service][href="#oferta"]').forEach(a=>{
  a.addEventListener('click',()=>selectOffer(a.dataset.service, false, false));
});
const menu=$('.menu-toggle');
const nav=$('#main-nav');
function closeMenu(){
  if (!menu || !nav) return;
  menu.setAttribute('aria-expanded','false');
  menu.setAttribute('aria-label','Otwórz menu');
  nav.classList.remove('open');
}
if (menu && nav) {
  menu.addEventListener('click',()=>{
    const open=menu.getAttribute('aria-expanded')!=='true';
    menu.setAttribute('aria-expanded',String(open));
    menu.setAttribute('aria-label',open?'Zamknij menu':'Otwórz menu');
    nav.classList.toggle('open',open);
  });
  $$('#main-nav a').forEach(a=>a.addEventListener('click',closeMenu));
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape' && menu.getAttribute('aria-expanded')==='true') {
      closeMenu(); menu.focus();
    }
  });
  document.addEventListener('click',e=>{
    if (!menu.contains(e.target) && !nav.contains(e.target)) closeMenu();
  });
  window.addEventListener('resize',()=>{if(window.innerWidth>1120)closeMenu()});
}
$$('#main-nav a').forEach(a=>{
  const url=new URL(a.href,window.location.href);
  const active=url.origin===window.location.origin && normalizePath(url.pathname)===pagePath;
  a.classList.toggle('active',active);
  if(active)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');
});
const header=$('.header');
if (header) {
  const updateHeader=()=>header.classList.toggle('scrolled',window.scrollY>15);
  updateHeader();
  window.addEventListener('scroll',updateHeader,{passive:true});
}
let days=15;
function updateCalc(){
  if (!$('#amount')) return;
  const amount=Number($('#amount').value),valid=Number.isFinite(amount)&&amount>=50&&amount<=100000;
  $('#amount-error').hidden=valid;$('#amount').setAttribute('aria-invalid',String(!valid));
  const rate=days===15?.025:.05,fee=Math.round(amount*rate*100)/100;
  $('#days-label').textContent=days+' dni';$('#rate-label').textContent=(days===15?'2,5':'5')+'% kwoty pożyczki';
  $('#fee').textContent=valid?money(fee):'—';$('#total').textContent=valid?money(Math.round((amount+fee)*100)/100):'—';
  $('#amount-range').max=amount>20000?'100000':'20000';$('#amount-range').value=valid?amount:50;
  $('.range-limits span:last-child').textContent=amount>20000?'100 000 zł':'20 000 zł';
  $$('[data-amount]').forEach(b=>{const active=valid&&Number(b.dataset.amount)===amount;b.classList.toggle('selected',active);b.setAttribute('aria-pressed',String(active))});
  const link=$('#calc-contact');link.setAttribute('aria-disabled',String(!valid));link.tabIndex=valid?0:-1;
  if(valid)link.href=whatsapp+'?text='+encodeURIComponent('Dzień dobry, interesuje mnie pożyczka pod zastaw w kwocie '+money(amount)+' na '+days+' dni. Kalkulator wskazał opłatę '+money(fee)+' i łącznie '+money(amount+fee)+' do spłaty. Proszę o potwierdzenie warunków.');else link.removeAttribute('href');
}
if ($('#amount')) {
$('#amount').addEventListener('input',updateCalc);$('#amount-range').addEventListener('input',e=>{$('#amount').value=e.target.value;updateCalc()});
$$('[data-amount]').forEach(b=>b.addEventListener('click',()=>{$('#amount').value=b.dataset.amount;updateCalc()}));
$$('[data-days]').forEach(b=>b.addEventListener('click',()=>{days=Number(b.dataset.days);$$('[data-days]').forEach(x=>{const active=x===b;x.classList.toggle('selected',active);x.setAttribute('aria-pressed',String(active))});updateCalc()}));updateCalc();
}
function openDialog(d){if(!d)return;d.showModal();document.body.classList.add('modal-open')}
$$('dialog').forEach(d=>{d.querySelector('.dialog-close')?.addEventListener('click',()=>d.close());d.addEventListener('close',()=>{if(!$('dialog[open]'))document.body.classList.remove('modal-open')});d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close()}})});
document.addEventListener('click',e=>{const trigger=e.target.closest('[data-inquiry]');if(!trigger || !$('#inquiry-dialog') || !$('#inquiry-subject'))return;$('#inquiry-subject').value=trigger.dataset.inquiry;openDialog($('#inquiry-dialog'))});
$('#inquiry-form')?.addEventListener('submit',e=>{e.preventDefault();const message=$('#inquiry-message').value.trim();if(!message){$('#inquiry-message').setCustomValidity('Opisz krótko przedmiot lub pytanie.');$('#inquiry-message').reportValidity();return}$('#inquiry-message').setCustomValidity('');const text='Dzień dobry! Interesuje mnie: '+$('#inquiry-subject').value+'.\n\n'+message;window.open(whatsapp+'?text='+encodeURIComponent(text),'_blank','noopener,noreferrer')});
$('#inquiry-message')?.addEventListener('input',e=>e.target.setCustomValidity(''));
const details={coins:{title:'Monety inwestycyjne',text:'Kupujemy i sprzedajemy monety ze złota oraz srebra. O dostępne egzemplarze i aktualne ceny zapytaj w SEZAM. Wycenę konkretnej monety potwierdzimy po sprawdzeniu jej parametrów i stanu.',tags:['Złote monety','Srebrne monety','Skup i sprzedaż']},bars:{title:'Sztabki złota i srebra',text:'W SEZAM możesz kupić lub sprzedać sztabki o różnej wadze. Sprawdzamy parametry i autentyczność przedmiotu, a cenę ustalamy na podstawie aktualnych warunków. Zapytaj nas o dostępność interesującej Cię gramatury.',tags:['Złoto','Srebro','Różne gramatury']},jewelry:{title:'Biżuteria z charakterem',text:'Pierścionki, łańcuszki, bransoletki, kolczyki, obrączki i zawieszki. Przyjdź do naszego punktu i zobacz biżuterię z bliska. Doradzimy w wyborze i odpowiemy na pytania o konkretny wyrób.',tags:['Pierścionki','Łańcuszki','Bransoletki','Kolczyki']}};
let infoKey='coins';$$('[data-info]').forEach(b=>b.addEventListener('click',()=>{infoKey=b.dataset.info;if(!Object.hasOwn(details,infoKey)||!$('#info-dialog'))return;const o=details[infoKey];$('#info-title').textContent=o.title;$('#info-text').textContent=o.text;$('#info-tags').replaceChildren(...o.tags.map(t=>{const s=document.createElement('span');s.textContent=t;return s}));openDialog($('#info-dialog'))}));
$('#info-contact')?.addEventListener('click',()=>{$('#info-dialog').close();$('#inquiry-subject').value=infoKey==='coins'?'Monety inwestycyjne':infoKey==='bars'?'Sztabki złota i srebra':'Zakup biżuterii';openDialog($('#inquiry-dialog'))});
function openingStatus(){if(!$('#open-status'))return;const parts=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Warsaw',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date());const p=Object.fromEntries(parts.map(x=>[x.type,x.value]));const end=p.weekday==='Sat'?14:p.weekday==='Sun'?0:18;const t=Number(p.hour)+Number(p.minute)/60;const open=end>0&&t>=10&&t<end;const status=$('#open-status');status.classList.toggle('open',open);status.querySelector('span:last-child').textContent=open?'Według grafiku: otwarte do '+end+':00':'Zapraszamy pn.–pt. 10–18, sob. 10–14'}
if ($('#open-status')) { openingStatus(); setInterval(openingStatus,60000); }
if ($('#year')) $('#year').textContent=new Date().getFullYear();
