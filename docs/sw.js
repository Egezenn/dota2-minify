var CACHE = "dota2-minify-v1";
var META_CACHE = "dota2-minify-meta-v1";
var CHECK_INTERVAL = 86400000;

self.addEventListener("install", function (e) {
  e.waitUntil(
    caches.open(CACHE).then(function (c) {
      return c.addAll([
        "./index.html",
        "./style.css",
        "./mirror.js",
        "./index.js",
        "./assets/logo.jpg",
        "./assets/favicon.ico",
      ]);
    }),
  );
  self.skipWaiting();
});

self.addEventListener("activate", function (e) {
  e.waitUntil(
    caches
      .keys()
      .then(function (ks) {
        return Promise.all(
          ks
            .filter(function (k) {
              return k !== CACHE && k !== META_CACHE;
            })
            .map(function (k) {
              return caches.delete(k);
            }),
        );
      })
      .then(function () {
        return self.clients.claim();
      }),
  );
});

self.addEventListener("fetch", function (e) {
  var url = new URL(e.request.url);

  if (url.origin !== self.location.origin || e.request.method !== "GET") return;

  var scopePath = new URL(self.registration.scope).pathname;
  var reqPath = url.pathname;

  var isIndex =
    reqPath === scopePath ||
    reqPath === scopePath + "index.html" ||
    reqPath === scopePath.slice(0, -1) ||
    reqPath === scopePath.slice(0, -1) + "/index.html";

  if (isIndex) {
    e.respondWith(
      caches.match(e.request).then(function (cached) {
        if (cached) {
          fetch(e.request)
            .then(function (r) {
              if (r.ok) {
                caches.open(CACHE).then(function (c) {
                  c.put(e.request, r);
                });
              }
            })
            .catch(function () {});
          return cached;
        }
        return fetch(e.request).then(function (r) {
          if (r.ok) {
            var clone = r.clone();
            caches.open(CACHE).then(function (c) {
              c.put(e.request, clone);
            });
          }
          return r;
        });
      }),
    );
    return;
  }

  if (
    url.pathname.endsWith(".js") ||
    url.pathname.endsWith(".css") ||
    url.pathname.endsWith(".jpg") ||
    url.pathname.endsWith(".jpeg") ||
    url.pathname.endsWith(".png") ||
    url.pathname.endsWith(".gif") ||
    url.pathname.endsWith(".svg") ||
    url.pathname.endsWith(".ico") ||
    url.pathname.endsWith(".woff") ||
    url.pathname.endsWith(".woff2")
  ) {
    e.respondWith(
      caches.match(e.request).then(function (cached) {
        var fetchPromise = fetch(e.request)
          .then(function (r) {
            if (r.ok) {
              var clone = r.clone();
              caches.open(CACHE).then(function (c) {
                c.put(e.request, clone);
              });
            }
            return r;
          })
          .catch(function () {
            return cached;
          });

        return cached || fetchPromise;
      }),
    );
  }
});

self.addEventListener("message", function (e) {
  if (e.data && e.data.type === "CHECK_UPDATE") {
    e.waitUntil(dailyCheck(false));
  }
  if (e.data && e.data.type === "FORCE_CHECK_UPDATE") {
    e.waitUntil(dailyCheck(true));
  }
  if (e.data && e.data.type === "CLEAR_CACHE") {
    e.waitUntil(
      caches.keys().then(function (ks) {
        return Promise.all(
          ks.map(function (k) {
            return caches.delete(k);
          }),
        );
      }),
    );
  }
});

async function dailyCheck(force) {
  if (!force) {
    var meta = await caches.open(META_CACHE);
    var last = await meta.match("last-check");

    if (last) {
      var ts = parseInt(await last.text());
      if (Date.now() - ts < CHECK_INTERVAL) return;
    }
  }

  var indexUrl = new URL("./index.html", self.location.href).href;

  try {
    var cache = await caches.open(CACHE);
    var cached = await cache.match(indexUrl);
    var r = await fetch(indexUrl, { cache: "no-store" });

    if (r.ok) {
      if (cached) {
        var oldText = await cached.text();
        var freshText = await r.text();

        if (oldText !== freshText) {
          await cache.put(
            indexUrl,
            new Response(freshText, {
              headers: { "Content-Type": "text/html" },
            }),
          );

          var clients = await self.clients.matchAll();
          clients.forEach(function (c) {
            c.postMessage({ type: "INDEX_UPDATED" });
          });
        }
      } else {
        await cache.put(indexUrl, r);
      }
    }
  } catch (_) {}

  await meta.put("last-check", new Response(Date.now().toString()));
}
