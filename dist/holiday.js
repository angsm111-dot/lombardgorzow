/* Falling stars, with a persistent pause control and reduced-motion support. */
(() => {
  const layer = document.querySelector('.holiday-snow');
  const toggle = document.querySelector('.snow-toggle');
  if (!layer || !toggle) return;
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mobile = window.matchMedia('(max-width:760px), (hover:none) and (pointer:coarse)');
  let scrolling = false;
  let resumeTimer;
  function syncPause() {
    layer.classList.toggle('paused', document.hidden || scrolling);
  }
  // Yield animation work to native touch scrolling, including momentum.
  // Passive listeners never cancel or replace the browser's scrolling.
  function pauseForScroll() {
    if (!mobile.matches || layer.hidden || document.hidden) return;
    if (!scrolling) { scrolling = true; syncPause(); }
    clearTimeout(resumeTimer);
    resumeTimer = setTimeout(() => { scrolling = false; syncPause(); }, 240);
  }
  window.addEventListener('scroll', pauseForScroll, { passive: true });
  window.addEventListener('touchstart', pauseForScroll, { passive: true });
  window.addEventListener('touchend', pauseForScroll, { passive: true });
  let enabled = true;
  try { enabled = localStorage.getItem('sezam-snow') !== 'off'; } catch {}
  for (let i = 0; i < 28; i++) {
    const flake = document.createElement('span');
    flake.className = 'snowflake';
    flake.style.cssText = `--x:${(i * 37 + 8) % 100}%;--size:${2 * (3 + i % 5)}px;--duration:${14 + i % 11}s;--delay:-${i * 1.73}s;--drift:${(i % 2 ? 1 : -1) * (18 + i % 6 * 8)}px;--opacity:${.38 + i % 5 * .09}`;
    layer.append(flake);
  }
  function render() {
    layer.hidden = !enabled || reduced.matches;
    if (layer.hidden || !mobile.matches) {
      clearTimeout(resumeTimer);
      scrolling = false;
    }
    syncPause();
    toggle.hidden = reduced.matches;
    toggle.textContent = enabled ? 'Wyłącz śnieg' : 'Włącz śnieg';
    toggle.setAttribute('aria-pressed', String(enabled));
  }
  toggle.addEventListener('click', () => {
    enabled = !enabled;
    try { localStorage.setItem('sezam-snow', enabled ? 'on' : 'off'); } catch {}
    render();
  });
  document.addEventListener('visibilitychange', syncPause);
  mobile.addEventListener('change', render);
  reduced.addEventListener('change', render);
  render();
})();
