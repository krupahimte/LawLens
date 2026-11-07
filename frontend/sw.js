/* Service worker: makes the app installable and lets the shell open offline.
 * It caches only the static app shell. Chat, PDFs and health checks always go to the network,
 * so legal answers are never served stale from a cache. */
const CACHE = "ila-shell-v5";   // bumped: editorial redesign, self-hosted fonts, new icons
const SHELL = ["/", "/static/app.css", "/static/app.js", "/manifest.webmanifest",
               "/static/icons/icon-192.png", "/static/icons/icon-512.png", "/static/icons/apple-touch-icon.png",
               "/static/fonts/inter.woff2", "/static/fonts/playfair-display.woff2", "/static/fonts/playfair-display-italic.woff2",
               "/static/fonts/plex-mono-400.woff2", "/static/fonts/plex-mono-500.woff2"];

self.addEventListener("install", e => {
  // Individual puts: one missing optional asset must not block installation of the whole shell.
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(SHELL.map(u => c.add(u).catch(() => {})))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  const isShell = SHELL.includes(url.pathname);
  if (!isShell) return;                                   // /chat, /pdf, /health: network only
  e.respondWith(
    fetch(req).then(res => {                              // network first, so updates show up
      const copy = res.clone();
      caches.open(CACHE).then(c => c.put(req, copy));
      return res;
    }).catch(() => caches.match(req))
  );
});
