(function () {
  "use strict";

  // TODO: Need to mirror community mods & use deployment URLs instead of raw
  var MIRRORS = {
    github: {
      name: "GitHub",
      hostname: "egezenn.github.io",
      siteBase: "https://egezenn.github.io/dota2-minify",
      releases: "https://github.com/egezenn/dota2-minify/releases",
      repo: "https://github.com/egezenn/dota2-minify",
      wiki: "https://egezenn.github.io/dota2-minify/wiki",
      api: {
        releases: "https://api.github.com/repos/egezenn/dota2-minify/releases",
        contents: "https://api.github.com/repos/egezenn/dota2-minify/contents",
        communityContents:
          "https://api.github.com/repos/egezenn/dota2-minify-community/contents",
      },
      raw: {
        base: "https://raw.githubusercontent.com/Egezenn/dota2-minify/main",
        communityBase:
          "https://raw.githubusercontent.com/Egezenn/dota2-minify-community/main",
      },
      ping: "https://api.github.com/repos/egezenn/dota2-minify",
    },
    codeberg: {
      name: "Codeberg",
      hostname: "egezenn.codeberg.page",
      siteBase: "https://egezenn.codeberg.page/dota2-minify",
      releases: "https://codeberg.org/egezenn/dota2-minify/releases",
      repo: "https://codeberg.org/egezenn/dota2-minify",
      wiki: "https://codeberg.org/egezenn/dota2-minify/wiki",
      api: {
        releases:
          "https://codeberg.org/api/v1/repos/egezenn/dota2-minify/releases",
        contents:
          "https://codeberg.org/api/v1/repos/egezenn/dota2-minify/contents",
        communityContents:
          "https://codeberg.org/api/v1/repos/egezenn/dota2-minify-community/contents",
      },
      raw: {
        base: "https://codeberg.org/egezenn/dota2-minify/raw/branch/main",
        communityBase:
          "https://codeberg.org/egezenn/dota2-minify-community/raw/branch/main",
      },
      ping: "https://codeberg.org/api/v1/repos/egezenn/dota2-minify",
    },
  };

  var PING_TIMEOUT = 5000;
  var DISMISS_KEY = "mirror-dismiss";
  var DISMISS_TTL = 86400000;

  var currentKey = "github";
  var currentMirror = MIRRORS.github;

  var hostname = window.location.hostname;
  for (var key in MIRRORS) {
    if (
      hostname === MIRRORS[key].hostname ||
      hostname.endsWith("." + MIRRORS[key].hostname)
    ) {
      currentKey = key;
      currentMirror = MIRRORS[key];
      break;
    }
  }

  window.Mirror = {
    current: currentMirror,
    currentKey: currentKey,
    reachable: true,

    getReleaseApiUrl: function () {
      return currentMirror.api.releases;
    },
    getContentsApiUrl: function (path) {
      return currentMirror.api.contents + "/" + path;
    },
    getRawUrl: function (path) {
      return currentMirror.raw.base + "/" + path;
    },
    getCommunityContentsApiUrl: function () {
      return currentMirror.api.communityContents;
    },
    getCommunityRawUrl: function (path) {
      return currentMirror.raw.communityBase + "/" + path;
    },
    getWikiUrl: function () {
      return currentMirror.wiki;
    },
    getRepoUrl: function () {
      return currentMirror.repo;
    },
    getReleasesUrl: function () {
      return currentMirror.releases;
    },
    getSiteBase: function () {
      return currentMirror.siteBase;
    },
  };

  document.querySelectorAll("[data-mirror]").forEach(function (el) {
    var mirrorKey = el.getAttribute("data-mirror");
    if (currentMirror[mirrorKey]) {
      el.href = currentMirror[mirrorKey];
    }
  });

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(function () {});
  }

  function ping(mirror) {
    return new Promise(function (resolve) {
      var ctrl = new AbortController();
      var timer = setTimeout(function () {
        ctrl.abort();
        resolve(false);
      }, PING_TIMEOUT);

      fetch(mirror.ping, {
        mode: "cors",
        signal: ctrl.signal,
        cache: "no-store",
      })
        .then(function (r) {
          clearTimeout(timer);
          resolve(r.ok);
        })
        .catch(function () {
          clearTimeout(timer);
          resolve(false);
        });
    });
  }

  function showModal(target) {
    var dismissed = localStorage.getItem(DISMISS_KEY);
    if (dismissed && Date.now() - parseInt(dismissed) < DISMISS_TTL) return;

    var el = document.getElementById("mirror-modal");
    if (!el) return;

    document.getElementById("mirror-modal-message").textContent =
      currentMirror.name +
      " is not reachable from your network. Would you like to switch to the " +
      target.name +
      " mirror?";
    document.getElementById("mirror-switch-btn").href = target.siteBase;
    document.getElementById("mirror-switch-btn").textContent =
      "Switch to " + target.name;
    document.getElementById("mirror-switch-btn").style.display = "";
    document.getElementById("mirror-dismiss-btn").textContent =
      "Stay on " + currentMirror.name;
    el.style.display = "flex";

    document.getElementById("mirror-dismiss-btn").onclick = function () {
      el.style.display = "none";
      localStorage.setItem(DISMISS_KEY, Date.now().toString());
    };
  }

  function showNoMirrorsModal() {
    var el = document.getElementById("mirror-modal");
    if (!el) return;

    document.getElementById("mirror-modal-message").textContent =
      "No mirrors are currently reachable. The site will continue to work with cached data.";
    document.getElementById("mirror-switch-btn").style.display = "none";
    document.getElementById("mirror-dismiss-btn").textContent = "OK";
    el.style.display = "flex";

    document.getElementById("mirror-dismiss-btn").onclick = function () {
      el.style.display = "none";
    };
  }

  (async function () {
    var working = await ping(currentMirror);

    if (working) {
      window.Mirror.reachable = true;
      navigator.serviceWorker.ready.then(function (reg) {
        if (reg.active) reg.active.postMessage({ type: "CHECK_UPDATE" });
      });
      return;
    }

    window.Mirror.reachable = false;

    for (var key in MIRRORS) {
      if (key === currentKey) continue;
      if (await ping(MIRRORS[key])) {
        showModal(MIRRORS[key]);
        return;
      }
    }

    showNoMirrorsModal();
  })();

  var qs = new URLSearchParams(window.location.search);

  if (qs.has("clear-cache")) {
    localStorage.removeItem("github-releases");
    localStorage.removeItem(DISMISS_KEY);
    sessionStorage.clear();
    navigator.serviceWorker.ready.then(function (reg) {
      if (reg.active) reg.active.postMessage({ type: "CLEAR_CACHE" });
    });
  }

  if (qs.has("force-check")) {
    navigator.serviceWorker.ready.then(function (reg) {
      if (reg.active) reg.active.postMessage({ type: "FORCE_CHECK_UPDATE" });
    });
  }
})();
