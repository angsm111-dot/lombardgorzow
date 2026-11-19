/* SEZAM public purchase-price integration.
 * Source: https://sezam.com.pl/skup-sprzedaz-zlota/ and
 * angsm111-dot/sezam.com.pl: dist/assets/classic.js, price-utils.mjs.
 * Prices in the public feed are FINAL PLN purchase prices. Never reapply margins,
 * infer an unlisted product's price from spot/scrap, or substitute stale rates.
 */
(() => {
  'use strict';
  const root = document.querySelector('.gold-pricing');
  if (!root) return;
  const PRICE_URL = 'https://skup-zlota-gorzow.angsm111.workers.dev/api/prices';
  const MAX_AGE = 15 * 60 * 1000, REFRESH_MS = 5 * 60 * 1000;
  const $ = id => document.getElementById(id);
  const money = value => new Intl.NumberFormat('pl-PL', { style: 'currency', currency: 'PLN' }).format(value);
  const decimal = value => new Intl.NumberFormat('pl-PL', { maximumFractionDigits: 4 }).format(value);
  const metals = { gold: 'złota', silver: 'srebra' };
  const metalButtons = [...root.querySelectorAll('[data-price-metal]')];
  const kindButtons = [...root.querySelectorAll('[data-price-kind]')];
  let metal = 'gold', kind = 'scrap', feed = null, loading = false, failed = false, rejectedStale = false;
  let lastAttempt = 0, expiryTimer = null;
  const selections = new Map();
  function current(data = feed) {
    if (!data || data.status !== 'ok' || typeof data.provider !== 'string' || /zapasowe|fallback/i.test(data.provider)) return false;
    const fetched = Date.parse(data.fetchedAt), now = Date.now();
    return Number.isFinite(fetched) && now - fetched <= MAX_AGE && fetched - now <= 5 * 60 * 1000 &&
      !!data.metals?.gold?.purities && !!data.metals?.silver?.purities && !!data.products;
  }
  function price(value) { return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : null; }
  function purities() {
    return current() ? Object.keys(feed.metals[metal].purities).filter(key => /^\d+(\.\d+)?$/.test(key) && price(feed.metals[metal].purities[key]?.price) !== null).sort((a, b) => Number(a) - Number(b)) : [];
  }
  function products() {
    const group = feed?.products?.[`${metal}${kind === 'coins' ? 'Coins' : 'Bars'}`];
    return current() && Array.isArray(group) ? group.filter(p => p && p.active !== false && typeof p.id === 'string' && typeof p.name === 'string') : [];
  }
  function remember() {
    // A disabled select contains temporary loading choices, not a user's choice.
    if (kind === 'scrap' && $('price-purity').disabled) return;
    selections.set(`${metal}:${kind}`, kind === 'scrap' ? $('price-purity').value : $('price-product').value);
  }
  function addOption(select, value, label) { select.add(new Option(label, value)); }
  function status() {
    const target = $('price-status');
    if (current()) {
      const date = new Intl.DateTimeFormat('pl-PL', { dateStyle: 'short', timeStyle: 'short', timeZone: 'Europe/Warsaw' }).format(new Date(feed.fetchedAt));
      target.textContent = `${failed ? 'Ostatni poprawny odczyt' : 'Cennik zaktualizowany'}: ${date}${failed ? ' · Nie udało się odświeżyć. Spróbujemy ponownie.' : ' · Odświeżanie co 5 minut'}`;
      target.dataset.state = failed ? 'warning' : 'ready';
    } else if (loading) {
      target.textContent = 'Pobieranie aktualnego cennika…'; target.dataset.state = 'loading';
    } else {
      const stale = rejectedStale || (feed && Date.now() - Date.parse(feed.fetchedAt) > MAX_AGE);
      target.textContent = stale ? 'Cennik wymaga aktualizacji. Zadzwoń lub zapytaj na WhatsApp o aktualną cenę.' : 'Aktualny cennik jest chwilowo niedostępny. Zadzwoń lub zapytaj na WhatsApp.';
      target.dataset.state = stale ? 'stale' : 'error';
    }
    $('price-refresh').disabled = loading;
    $('price-refresh').setAttribute('aria-busy', String(loading));
  }
  function renderTable() {
    const head = $('price-table-head'), body = $('price-table-body');
    head.replaceChildren(); body.replaceChildren();
    const header = document.createElement('tr');
    const labels = metal === 'gold' ? ['Próba złota', 'Zawartość złota', 'Cena za gram'] : ['Próba srebra', 'Cena za gram'];
    labels.forEach(label => { const th = document.createElement('th'); th.scope = 'col'; th.textContent = label; header.append(th); });
    head.append(header);
    const keys = purities();
    if (!keys.length) {
      const row = document.createElement('tr'), cell = document.createElement('td'); cell.colSpan = labels.length;
      cell.textContent = loading ? 'Pobieranie aktualnych cen…' : 'Zapytaj o aktualną cenę skupu.'; row.append(cell); body.append(row); return;
    }
    keys.forEach(key => {
      const row = document.createElement('tr');
      if (metal === 'gold' && key === '585') row.className = 'price-popular';
      const values = metal === 'gold' ? [key, `${decimal(Number(key) / 10)}%`, money(feed.metals[metal].purities[key].price)] : [key, money(feed.metals[metal].purities[key].price)];
      values.forEach((value, index) => { const cell = document.createElement(index ? 'td' : 'th'); if (!index) cell.scope = 'row'; cell.textContent = value; row.append(cell); });
      body.append(row);
    });
  }
  function renderProductList() {
    const list = $('price-product-list'), scroll = list.scrollTop;
    const normalize = text => text.toLocaleLowerCase('pl').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/ł/g, 'l');
    const query = kind === 'coins' ? normalize($('price-search').value.trim()) : '';
    const items = products().filter(item => normalize(item.name).includes(query));
    list.replaceChildren();
    if (!items.length) {
      const text = document.createElement('p'); text.className = 'price-help'; text.textContent = loading ? 'Pobieranie listy…' : query ? 'Nie znaleziono monety. Zmień nazwę lub wybierz „Inna moneta”.' : 'Zapytaj nas o aktualny cennik i dostępne pozycje.'; list.append(text);
    }
    if (kind === 'coins') items.push({ id: 'other', name: 'Inna moneta / nie ma jej na liście' });
    items.forEach(item => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'price-product-row'; button.dataset.productId = item.id;
      button.setAttribute('aria-pressed', String($('price-product').value === item.id));
      const name = document.createElement('span'); name.textContent = item.name;
      const rate = document.createElement('strong'); rate.textContent = price(item.price) === null ? 'Zapytaj o cenę' : money(item.price);
      button.append(name, rate); list.append(button);
    });
    list.scrollTop = scroll;
  }
  function renderControls() {
    const scrap = kind === 'scrap', saved = selections.get(`${metal}:${kind}`);
    root.dataset.metal = metal; root.dataset.kind = kind;
    metalButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.priceMetal === metal)));
    kindButtons.forEach(button => { const selected = button.dataset.priceKind === kind; button.setAttribute('aria-selected', String(selected)); button.tabIndex = selected ? 0 : -1; });
    $('price-panel').setAttribute('aria-labelledby', `price-tab-${kind}`);
    $('price-scrap-view').hidden = !scrap; $('price-products-view').hidden = scrap;
    $('price-purity-field').hidden = !scrap; $('price-weight-field').hidden = !scrap;
    $('price-product-field').hidden = scrap; $('price-quantity-field').hidden = scrap;
    $('price-search-field').hidden = kind !== 'coins';
    $('price-table-title').textContent = scrap ? `Cennik skupu ${metals[metal]}` : `Skup ${metal === 'gold' ? 'złotych' : 'srebrnych'} ${kind === 'coins' ? 'monet' : 'sztabek'}`;
    $('price-table-caption').textContent = `Aktualne ceny skupu ${metals[metal]} za gram`;
    $('price-unit').textContent = scrap ? 'PLN / g' : 'PLN / szt.';
    const select = $(scrap ? 'price-purity' : 'price-product'); select.replaceChildren();
    if (scrap) {
      root.querySelector('label[for="price-purity"]').textContent = `Próba ${metals[metal]}`;
      const keys = purities(); keys.forEach(key => addOption(select, key, `Próba ${key}`));
      addOption(select, 'unknown', 'Nie znam próby');
      select.value = [...select.options].some(option => option.value === saved) ? saved : keys.includes(metal === 'gold' ? '585' : '925') ? (metal === 'gold' ? '585' : '925') : keys[0] || 'unknown';
      select.disabled = !keys.length;
    } else {
      root.querySelector('label[for="price-product"]').textContent = kind === 'coins' ? 'Wybierz monetę' : 'Waga jednej sztabki';
      addOption(select, '', kind === 'coins' ? 'Wybierz monetę z listy' : 'Wybierz gramaturę');
      products().forEach(item => addOption(select, item.id, item.name));
      if (kind === 'coins') addOption(select, 'other', 'Inna moneta / nie ma jej na liście');
      if ([...select.options].some(option => option.value === saved)) select.value = saved;
      select.disabled = !current() && kind !== 'coins';
    }
    renderTable(); renderProductList(); updateQuote();
  }
  function updateQuote() {
    const scrap = kind === 'scrap', unknown = scrap && $('price-purity').value === 'unknown', other = kind === 'coins' && $('price-product').value === 'other';
    $('price-other-field').hidden = !other;
    const input = $(scrap ? 'price-weight' : 'price-quantity');
    const quantity = input.valueAsNumber;
    const validQuantity = Number.isFinite(quantity) && quantity > 0 && quantity <= (scrap ? 100000 : 10000) && (scrap || Number.isInteger(quantity));
    input.setAttribute('aria-invalid', String(!validQuantity));
    let unit = null, name = '';
    if (current()) {
      if (scrap) unit = price(feed.metals[metal].purities[$('price-purity').value]?.price);
      else { const product = products().find(item => item.id === $('price-product').value); unit = price(product?.price); name = product?.name || ''; }
    }
    // The API's product price is per piece; scrap is per gram. No extra margin.
    const total = unit !== null && validQuantity ? Math.round((unit * quantity + Number.EPSILON) * 100) / 100 : null;
    const displayTotal = total !== null && Number.isFinite(total) ? total : null;
    $('price-total').textContent = displayTotal === null ? (current() && (unknown || other || (!scrap && $('price-product').value)) ? 'Wycena indywidualna' : '—') : money(displayTotal);
    $('price-total').classList.toggle('price-total-message', displayTotal === null);
    let help = 'Wybierz przedmiot, aby sprawdzić cenę.';
    if (!current()) help = loading ? 'Pobieranie aktualnych cen…' : 'Cennik chwilowo niedostępny. Zapytaj o aktualną cenę.';
    else if (unknown) help = 'Nie znasz próby? Sprawdzimy ją na miejscu.';
    else if (other) help = 'Opisz monetę lub dołącz jej zdjęcie w rozmowie na WhatsApp.';
    else if (!validQuantity) help = scrap ? 'Wpisz wagę większą od zera, nie większą niż 100 000 g.' : 'Wpisz całkowitą liczbę sztuk od 1 do 10 000.';
    else if (displayTotal !== null) help = `${money(unit)} / ${scrap ? 'g' : 'szt.'} · Ostateczna wycena po sprawdzeniu przedmiotu.`;
    else if (!scrap && $('price-product').value) help = 'Zapytaj o cenę wybranego przedmiotu.';
    $('price-result-help').textContent = help;
    root.querySelectorAll('[data-product-id]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.productId === $('price-product').value)));
    const details = scrap ? `Próba: ${unknown ? 'nieznana' : $('price-purity').value || 'do ustalenia'}.${validQuantity ? ` Waga: ${decimal(quantity)} g.` : ''}` : `${name || (other ? $('price-other-name').value.trim() || 'inna moneta' : 'przedmiot do ustalenia')}.${validQuantity ? ` Liczba sztuk: ${quantity}.` : ''}`;
    const text = `Dzień dobry, proszę o wycenę ${metals[metal]}. ${details}${displayTotal === null ? '' : ` Orientacyjna wartość według cennika: ${money(displayTotal)}.`}`;
    $('price-whatsapp').href = `https://wa.me/48601775146?text=${encodeURIComponent(text)}`;
  }
  function render() { status(); renderControls(); }
  async function refresh() {
    if (loading) return;
    loading = true; lastAttempt = Date.now(); render();
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), 12000);
    try {
      const response = await fetch(PRICE_URL, { cache: 'no-store', credentials: 'omit', signal: controller.signal });
      if (!response.ok) throw new Error('Prices unavailable');
      const next = await response.json();
      if (!current(next)) { rejectedStale = Number.isFinite(Date.parse(next?.fetchedAt)) && Date.now() - Date.parse(next.fetchedAt) > MAX_AGE; throw new Error('Invalid or stale prices'); }
      feed = next; failed = false; rejectedStale = false;
      clearTimeout(expiryTimer);
      expiryTimer = setTimeout(() => { remember(); render(); }, Math.max(0, Date.parse(feed.fetchedAt) + MAX_AGE - Date.now() + 50));
    } catch { failed = true; }
    finally { clearTimeout(timeout); loading = false; render(); }
  }
  function selectMetal(value) { remember(); metal = value; $('price-search').value = ''; render(); }
  function selectKind(value) { remember(); kind = value; $('price-search').value = ''; render(); }
  metalButtons.forEach((button, index) => {
    button.addEventListener('click', () => selectMetal(button.dataset.priceMetal));
    button.addEventListener('keydown', event => { if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); const next = metalButtons[1 - index]; next.focus(); selectMetal(next.dataset.priceMetal); } });
  });
  kindButtons.forEach((button, index) => {
    button.addEventListener('click', () => selectKind(button.dataset.priceKind));
    button.addEventListener('keydown', event => {
      const next = event.key === 'ArrowRight' ? (index + 1) % kindButtons.length : event.key === 'ArrowLeft' ? (index + kindButtons.length - 1) % kindButtons.length : event.key === 'Home' ? 0 : event.key === 'End' ? kindButtons.length - 1 : null;
      if (next !== null) { event.preventDefault(); kindButtons[next].focus(); selectKind(kindButtons[next].dataset.priceKind); }
    });
  });
  $('metal-calculator').addEventListener('submit', event => event.preventDefault());
  $('metal-calculator').addEventListener('input', () => { remember(); updateQuote(); });
  $('price-product').addEventListener('change', () => { remember(); $('price-search').value = ''; renderProductList(); updateQuote(); });
  $('price-product-list').addEventListener('click', event => {
    const button = event.target.closest('[data-product-id]');
    if (!button) return;
    $('price-product').value = button.dataset.productId; remember(); updateQuote();
  });
  $('price-search').addEventListener('input', renderProductList);
  $('price-refresh').addEventListener('click', () => { remember(); refresh(); });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) { remember(); render(); if (Date.now() - lastAttempt >= REFRESH_MS) refresh(); } });
  setInterval(() => { remember(); refresh(); }, REFRESH_MS);
  render(); refresh();
})();
