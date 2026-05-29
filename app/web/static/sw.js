const CACHE_NAME = "rmosoft-pos-v1";

const CORE_ASSETS = [
  "/admin/pos",
  "/static/manifest.json"
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CORE_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((k) => (k !== CACHE_NAME ? caches.delete(k) : null)))
    )
  );
  self.clients.claim();
});

// Estrategia: network-first para HTML, cache-first para estáticos
self.addEventListener("fetch", (event) => {
  const req = event.request;
  const url = new URL(req.url);

  // Solo tu dominio
  if (url.origin !== location.origin) return;

  // HTML -> network first (para que actualice)
  if (req.headers.get("accept")?.includes("text/html")) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Estáticos -> cache first
  event.respondWith(
    caches.match(req).then((cached) => cached || fetch(req))
  );
});