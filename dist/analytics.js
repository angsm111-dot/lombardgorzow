/* Preserve the existing production GTM container; preview/comparison pages stay outside analytics. */
(() => {
  if (!['lombardgorzow.com', 'www.lombardgorzow.com'].includes(location.hostname)) return;
  if (/noindex|none/i.test(document.querySelector('meta[name="robots"]')?.content || '')) return;
  window.dataLayer = window.dataLayer || [];
  window.dataLayer.push({'gtm.start': Date.now(), event: 'gtm.js'});
  const script = document.createElement('script');
  script.async = true;
  script.src = 'https://www.googletagmanager.com/gtm.js?id=GTM-WMGWJNX';
  document.head.appendChild(script);
})();
