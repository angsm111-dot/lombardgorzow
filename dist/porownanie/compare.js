(()=>{
  'use strict';
  const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
  const cards=$$('.version-card'),frames=$$('iframe'),grid=$('#comparison-grid'),picker=$('#section-picker'),sync=$('#sync-scroll');
  const sectionIds=['main','oferta','kalkulator','o-nas','pytania','kontakt'];
  const names=Object.fromEntries(cards.map(card=>[card.dataset.version,card.dataset.label||card.querySelector('h2').textContent.trim()]));
  let view='all',device='desktop',raf=0,pausedUntil=0;
  const expandIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-7 7M10 20H4v-6M4 20l7-7"/></svg>';
  const suppressed=new WeakMap();
  function fit(){
    pausedUntil=performance.now()+250;
    cards.forEach(card=>{
      const stage=card.querySelector('.stage'),frame=stage.querySelector('iframe');
      const viewport=device==='mobile'?390:1360;
      if(card.hidden){frame.style.width=viewport+'px';frame.style.height=(device==='mobile'?844:930)+'px';return;}
      const scale=Math.min(stage.clientWidth/viewport,1);
      const height=view==='all'?(device==='mobile'?720:930*scale):Math.max(430,Math.min(900,window.innerHeight-175));
      stage.style.height=height+'px';
      frame.style.width=viewport+'px';frame.style.height=(height/scale)+'px';
      frame.style.left='50%';frame.style.marginLeft=(-viewport*scale/2)+'px';
      frame.style.transform=`scale(${scale})`;
    });
  }
  function setView(next){
    const section=picker.value;
    pausedUntil=performance.now()+250;cancelAnimationFrame(raf);
    view=next;grid.classList.toggle('single',view!=='all');
    cards.forEach(card=>{card.hidden=view!=='all'&&card.dataset.version!==view;const b=card.querySelector('[data-expand]');b.innerHTML=(view==='all'?'Powiększ':'Wszystkie wersje')+expandIcon;});
    $$('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)));
    sync.disabled=view!=='all';
    $('#view-hint').textContent=view==='all'?(sync.checked?'Podglądy obok siebie. Przewijaj dowolny podgląd — pozostałe podążą za nim.':'Każdy projekt przewijasz osobno. Wybierz sekcję, aby porównać ten sam temat we wszystkich.'):names[view]+' · Duży podgląd. Przełącz wersję u góry, aby zobaczyć różnicę w tym samym miejscu.';
    fit();
    requestAnimationFrame(()=>jump(section));
    const url=new URL(location.href);url.searchParams.set('widok',view);url.searchParams.set('ekran',device);history.replaceState(null,'',url);
  }
  function anchors(frame){
    const w=frame.contentWindow,d=frame.contentDocument;if(!d?.querySelector('main'))return [];
    return sectionIds.filter(id=>d.getElementById(id)).map(id=>({id,y:id==='main'?0:Math.max(0,d.getElementById(id).getBoundingClientRect().top+w.scrollY-(device==='mobile'?82:98))})).sort((a,b)=>a.y-b.y);
  }
  function scrollTo(frame,y){suppressed.set(frame,performance.now()+120);frame.contentWindow.scrollTo({top:y,behavior:'instant'});}
  function jump(id){frames.forEach(f=>{const a=anchors(f).find(a=>a.id===id);if(a)scrollTo(f,a.y)});}
  function syncFrom(source){
    if(!sync.checked||source.closest('.version-card').hidden||performance.now()<pausedUntil||performance.now()<(suppressed.get(source)||0))return;
    cancelAnimationFrame(raf);raf=requestAnimationFrame(()=>{
      const a=anchors(source),y=source.contentWindow.scrollY;if(!a.length)return;
      let index=0;for(let i=0;i<a.length;i++)if(y>=a[i].y-2)index=i;
      const end=a[index+1]?.y??Math.max(a[index].y+1,source.contentDocument.documentElement.scrollHeight-source.contentWindow.innerHeight);
      const fraction=Math.max(0,Math.min(1,(y-a[index].y)/(end-a[index].y||1)));
      picker.value=a[index].id;
      frames.filter(f=>f!==source).forEach(f=>{const b=anchors(f),target=b.findIndex(x=>x.id===a[index].id);if(target<0)return;const targetEnd=b[target+1]?.y??Math.max(b[target].y+1,f.contentDocument.documentElement.scrollHeight-f.contentWindow.innerHeight);scrollTo(f,b[target].y+fraction*(targetEnd-b[target].y));});
    });
  }
  frames.forEach(frame=>{
    function ready(){
      if(!frame.contentDocument?.querySelector('main'))return;
      frame.closest('.stage').classList.add('loaded');
      frame.contentWindow.addEventListener('scroll',()=>syncFrom(frame),{passive:true});
      frame.contentDocument.querySelectorAll('a[href^="http"],a[href^="tel:"]').forEach(a=>{a.target='_blank';a.rel='noopener';});
      const a=anchors(frame).find(a=>a.id===picker.value);if(a)scrollTo(frame,a.y);
    }
    frame.addEventListener('load',ready);if(frame.contentDocument?.readyState==='complete')ready();
  });
  $$('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
  $$('[data-expand]').forEach(b=>b.addEventListener('click',()=>{setView(view==='all'?b.dataset.expand:'all');$('.controls').scrollIntoView({behavior:'smooth',block:'start'});}));
  $$('[data-device]').forEach(b=>b.addEventListener('click',()=>{device=b.dataset.device;grid.classList.toggle('mobile',device==='mobile');$$('[data-device]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));setView(view);}));
  picker.addEventListener('change',()=>jump(picker.value));
  $('#reset').addEventListener('click',()=>{picker.value='main';jump('main')});
  sync.addEventListener('change',()=>{if(sync.checked)jump(picker.value);$('#view-hint').textContent=sync.checked?'Przewijaj dowolny podgląd — pozostałe podążą za nim.':'Każdy projekt przewijasz osobno. Wybierz sekcję, aby porównać ten sam temat we wszystkich.';});
  new ResizeObserver(fit).observe(grid);
  const params=new URLSearchParams(location.search);
  if(params.get('ekran')==='mobile'){device='mobile';grid.classList.add('mobile');$$('[data-device]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.device===device)));}
  setView(Object.hasOwn(names,params.get('widok'))?params.get('widok'):'all');
})();
