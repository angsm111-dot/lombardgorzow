import { defineConfig } from 'vite';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
const routes = ['impuls-wersje','wersja-6','wersja-7','wersja-8','wersja-9','wersja-10','wersje','wersja-1','wersja-2','wersja-3','wersja-4','wersja-5','gotowka','skup-zlota','telefony-laptopy','serwis-gsm','czesci','na-sprzedaz','o-nas','kontakt','pytania','galeria','blog'];
export default defineConfig({
  base: process.env.SITE_BASE || '/',
  plugins: [{ name: 'static-pages', async closeBundle() {
    const html = await readFile('dist/index.html','utf8');
    for (const route of routes) { await mkdir(`dist/${route}`,{recursive:true}); await writeFile(`dist/${route}/index.html`,html); }
    await writeFile('dist/404.html',html);
  }}],
});
