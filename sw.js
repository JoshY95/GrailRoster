const CACHE = "grailroster-vault-v22";
const ASSETS = ["./", "index.html", "theme.css", "styles.css", "vault.css?v=19", "ui.js", "vault.js?v=19", "config.js", "app.js?v=19", "manifest.json", "data/catalogue-index.json", "data/images.json"];

self.addEventListener("install", (event) => event.waitUntil((async () => {
  const cache = await caches.open(CACHE);
  const response = await fetch("data/catalogue-index.json", {cache: "reload"});
  if (!response.ok) throw new Error("Catalogue index failed to cache");
  const index = await response.json();
  const assets = [...ASSETS, ...index.sets.map(set => `data/${set.file}`)];
  await cache.addAll(assets.map(url => new Request(url, {cache: "reload"})));
  await self.skipWaiting();
})()));
self.addEventListener("activate", (event) => event.waitUntil(caches.keys()
  .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
  .then(() => self.clients.claim())));
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  if (new URL(event.request.url).origin !== self.location.origin) return;
  event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request).then((response) => {
    const copy = response.clone();
    caches.open(CACHE).then((cache) => cache.put(event.request, copy));
    return response;
  })));
});
