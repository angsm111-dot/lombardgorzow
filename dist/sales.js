/* Progressive enhancement only: full categories, offers and galleries work without JS. */
(() => {
  'use strict';
  document.querySelectorAll('.sales-gallery').forEach(gallery => {
    const main = gallery.querySelector('.sales-main-image');
    const image = main?.querySelector('img');
    if (!main || !image) return;
    gallery.querySelectorAll('.sales-thumbnails a').forEach(link => {
      link.addEventListener('click', event => {
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        const target = new URL(link.href, location.href);
        if (target.origin !== location.origin || !/^\/assets\/sales-feed-[a-f0-9]{64}\.(jpg|png|webp)$/.test(target.pathname)) return;
        event.preventDefault();
        image.src = target.pathname;
        main.href = target.pathname;
        gallery.querySelectorAll('.sales-thumbnails a').forEach(item => item.removeAttribute('aria-current'));
        link.setAttribute('aria-current', 'true');
      });
    });
  });
  const grid = document.querySelector('.sales-grid');
  if (!grid) return;
  const cards = [...grid.children];
  if (cards.length <= 24) return;
  let visible = 24;
  const more = document.createElement('button');
  more.type = 'button'; more.className = 'sales-more';
  more.textContent = 'Pokaż kolejne przedmioty';
  const update = () => {
    cards.forEach((card, index) => { card.hidden = index >= visible; });
    more.hidden = visible >= cards.length;
  };
  more.addEventListener('click', () => {
    const next = cards[visible]?.querySelector('a');
    visible += 24; update(); next?.focus({preventScroll: true});
  });
  grid.after(more); update();
})();
