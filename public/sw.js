const CACHE_NAME = 'osint-brutalist-v1';
const ASSETS = ['/', '/index.html', '/public/manifest.json'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Let API requests pass through to the serverless backend
  if (e.request.url.includes('/api/')) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then((res) => res || fetch(e.request))
  );
});