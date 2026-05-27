// Kazi Links — Service Worker for Web Push Notifications + offline shell
// Lightweight; no Workbox to keep PWA install small.

const CACHE = "kazi-links-v1";

self.addEventListener("install", (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(["/manifest.json"])).catch(() => null)
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

// Receive a push event and show a notification.
// Server sends { title, body, icon, url } in the push payload.
self.addEventListener("push", (event) => {
  let payload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch (e) {
    payload = { title: "Kazi Links", body: event.data ? event.data.text() : "" };
  }
  const title = payload.title || "Kazi Links";
  const options = {
    body: payload.body || "",
    icon: payload.icon || "/icon-192.png",
    badge: payload.badge || "/icon-192.png",
    data: { url: payload.url || "/", ...payload.data },
    tag: payload.tag || "kazi-links-notify",
    renotify: true,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

// On click, focus an existing tab or open the target URL.
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if ("focus" in w) {
          w.navigate(targetUrl).catch(() => null);
          return w.focus();
        }
      }
      if (self.clients.openWindow) return self.clients.openWindow(targetUrl);
      return null;
    })
  );
});
