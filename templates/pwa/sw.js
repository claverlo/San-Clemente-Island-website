{% load static %}// SCI Connect app worker. Pages always come from the network so website changes show up in the app right away;
// the offline page is only used when the phone has no signal.
const CACHE = 'sci-connect-v1';
const OFFLINE_URL = '{% url "offline" %}';
const OFFLINE_ASSETS = [OFFLINE_URL, '{% static "icons/icon-192.png" %}'];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(OFFLINE_ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  if (event.request.mode !== 'navigate') return;
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE_URL)));
});
