import gzip
import io
import json
import os
import re
import threading
import time
from urllib.parse import quote, unquote, urlparse

import requests
from core import base, config, fs, output, utils

# D2PFX Browser Constants
BASE_URL = "https://raw.githubusercontent.com/h6rd/Dota2PornFxWeb/data/"
ASSETS_URL = "https://raw.githubusercontent.com/h6rd/Dota2PornFxWeb/main/assets/files/"
PREVIEWS_URL = "https://raw.githubusercontent.com/h6rd/Dota2PornFxWeb/main/assets/previews/"

# Hugging Face fallback
HF_DATA_URL = "https://huggingface.co/datasets/hrdq/Dota2PornFx/resolve/data/data/"
HF_ASSETS_URL = "https://huggingface.co/datasets/hrdq/Dota2PornFx/resolve/main/assets/files/"
HF_PREVIEWS_URL = "https://huggingface.co/datasets/hrdq/Dota2PornFx/resolve/main/assets/previews/"

# GitHub Releases (primary source)
RELEASES_MANIFEST_URLS = [
    "https://raw.githubusercontent.com/h6rd/Dota2PornFx/main/manifest.json",
    "https://huggingface.co/datasets/hrdq/Dota2PornFx/resolve/main/manifest.json",
    "https://cdn.jsdelivr.net/gh/h6rd/Dota2PornFx@main/manifest.json",
]
MANIFEST_CACHE_NAME = "releases-manifest.json"
MANIFEST_URL_FIELDS = ("url", "download_url", "browser_download_url")
MANIFEST_RETRY_DELAY = 60

URL_FALLBACK_MAP = [
    (ASSETS_URL, HF_ASSETS_URL),
    (PREVIEWS_URL, HF_PREVIEWS_URL),
]

CACHE_DIR = os.path.join(base.cache_dir, "plugins", "d2pfx")
BLACKLIST = [
    "guides",
    "item-sounds",
    "news",
    "optimization",
    "tools",
    "sites",
    "packs",
    "fonts",
    "huds",  # Contains direct panorama overrides
]


class DataManager:
    HOST_REACHABLE_CACHE = {}
    REACHABILITY_TTL = 60
    NOTIFIED_HOSTS = set()
    _STATE_LOCK = threading.Lock()
    _RELEASE_LOCK = threading.Lock()
    _RELEASE_INDEX = None
    _RELEASE_FAILED_AT = 0

    def __init__(self):
        self.cache_dir = CACHE_DIR
        fs.create_dirs(self.cache_dir)
        self.metadata = {}
        self.constants = {}

    @staticmethod
    def to_hf_fallback(url):
        if not url:
            return None
        for gh_prefix, hf_prefix in URL_FALLBACK_MAP:
            if url.startswith(gh_prefix):
                return hf_prefix + url[len(gh_prefix) :]
        return None

    @staticmethod
    def _is_release_url(url):
        return bool(url) and url.startswith("https://github.com/") and "/releases/download/" in url

    @staticmethod
    def _source_label(url):
        host = urlparse(url).netloc
        if "huggingface.co" in host:
            return "the Hugging Face mirror"
        if DataManager._is_release_url(url):
            return "GitHub Releases"
        if "githubusercontent.com" in host:
            return "GitHub"
        return host

    @classmethod
    def is_url_reachable(cls, url, timeout=3):
        host = urlparse(url).netloc
        with cls._STATE_LOCK:
            cached = cls.HOST_REACHABLE_CACHE.get(host)
            now = time.time()
            if cached and (now - cached[1]) < cls.REACHABILITY_TTL:
                return cached[0]

            try:
                if cls._is_release_url(url):
                    # HEAD on release assets is unreliable (signed redirect), probe with a 1-byte GET.
                    # Any answer below 500 means the host is up, a 404 only means this file is missing.
                    with requests.get(
                        url, headers={"Range": "bytes=0-0"}, timeout=timeout, stream=True, allow_redirects=True
                    ) as response:
                        reachable = response.status_code < 500
                else:
                    response = requests.head(url, timeout=timeout, allow_redirects=True)
                    response.raise_for_status()
                    reachable = True
            except Exception:
                reachable = False

            cls.HOST_REACHABLE_CACHE[host] = (reachable, now)
            return reachable

    @classmethod
    def notify_fallback_once(cls, failed_url, target="the Hugging Face mirror"):
        host = urlparse(failed_url).netloc
        with cls._STATE_LOCK:
            if host in cls.NOTIFIED_HOSTS:
                return
            cls.NOTIFIED_HOSTS.add(host)
        output.add_text(f"{host} unreachable, D2PFX is using {target}", msg_type="info")

    # GitHub Releases manifest
    @staticmethod
    def _manifest_key(value):
        v = unquote(str(value or "").replace("\\", "/")).lstrip("/")
        return re.sub(r"\s+", ".", v.lower())

    @classmethod
    def _index_manifest(cls, node, index):
        if isinstance(node, list):
            for item in node:
                cls._index_manifest(item, index)
            return
        if not isinstance(node, dict):
            return

        url = next(
            (node[f] for f in MANIFEST_URL_FIELDS if isinstance(node.get(f), str) and node[f].startswith("http")), None
        )
        if url:
            category = node.get("category") if isinstance(node.get("category"), str) else ""
            # "name" is the original file name from mods.json, "asset" is the name inside the release
            for field, overwrite in (("name", True), ("asset", False)):
                value = node.get(field)
                if not isinstance(value, str) or not value:
                    continue
                key = cls._manifest_key(f"{category}/{value}" if category and "/" not in value else value)
                if overwrite:
                    index[key] = url
                else:
                    index.setdefault(key, url)
            return

        for value in node.values():
            if isinstance(value, (dict, list)):
                cls._index_manifest(value, index)

    def fetch_release_manifest(self, force_refresh=False):
        local_path = os.path.join(self.cache_dir, MANIFEST_CACHE_NAME)

        def _read_cache():
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None

        if not force_refresh and os.path.exists(local_path):
            cached = _read_cache()
            if cached is not None:
                return cached

        for url in RELEASES_MANIFEST_URLS:
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                data = response.json()
            except Exception:
                continue
            try:
                with open(local_path, "w", encoding="utf-8") as out:
                    json.dump(data, out)
            except Exception:
                pass
            return data

        # network failed: stale cache is better than nothing
        return _read_cache() if os.path.exists(local_path) else None

    def _ensure_release_index(self, force=False):
        cls = type(self)
        with cls._RELEASE_LOCK:
            if cls._RELEASE_INDEX is not None and not force:
                return cls._RELEASE_INDEX
            if not force and (time.time() - cls._RELEASE_FAILED_AT) < MANIFEST_RETRY_DELAY:
                return {}

            data = self.fetch_release_manifest(force_refresh=force)
            if data is None:
                cls._RELEASE_FAILED_AT = time.time()
                return cls._RELEASE_INDEX or {}

            index = {}
            self._index_manifest(data, index)
            cls._RELEASE_INDEX = index
            return index

    def get_release_url(self, cat_id, filename):
        index = self._ensure_release_index()
        if not index:
            return None
        return index.get(self._manifest_key(f"{cat_id}/{filename}")) or index.get(self._manifest_key(filename))

    def get_file_urls(self, cat_id, filename):
        path = f"{cat_id}/{quote(filename, safe='/')}"
        urls = []
        release_url = self.get_release_url(cat_id, filename)
        if release_url:
            urls.append(release_url)
        urls.append(f"{HF_ASSETS_URL}{path}")
        urls.append(f"{ASSETS_URL}{path}")
        return urls

    def get_download_urls(self, cat_id, file_or_url):
        if file_or_url.startswith("http"):
            if file_or_url.startswith(ASSETS_URL):
                rest = unquote(file_or_url[len(ASSETS_URL) :])
                rest_cat, _, rest_name = rest.partition("/")
                if rest_name:
                    return self.get_file_urls(rest_cat, rest_name)
            urls = [file_or_url]
            hf = self.to_hf_fallback(file_or_url)
            if hf:
                urls.append(hf)
            return urls
        return self.get_file_urls(cat_id, file_or_url)

    def download_urls(self, urls, dest, progress_tag=None, name=None, emit_progress=True):
        urls = list(dict.fromkeys(u for u in urls if u))
        for i, url in enumerate(urls):
            has_next = i < len(urls) - 1
            if has_next and not self.is_url_reachable(url):
                self.notify_fallback_once(url, self._source_label(urls[i + 1]))
                continue
            if fs.download_file(url, dest, progress_tag=progress_tag, name=name, emit_progress=emit_progress):
                return True
            if has_next:
                self.notify_fallback_once(url, self._source_label(urls[i + 1]))
        return False

    def download_file(self, url, dest, progress_tag=None, name=None, emit_progress=True, fallback_url=None):
        fallback_url = fallback_url or self.to_hf_fallback(url)
        urls = [url] + ([fallback_url] if fallback_url and fallback_url != url else [])
        return self.download_urls(urls, dest, progress_tag, name, emit_progress)

    def fetch_gz_json(self, filename, force_refresh=False):
        local_path = os.path.join(self.cache_dir, filename.replace(".gz", ""))
        gh_url = f"{BASE_URL}data/{filename}"
        hf_url = f"{HF_DATA_URL}{filename}"

        if not force_refresh and os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        if self.is_url_reachable(gh_url):
            candidate_urls = [gh_url, hf_url]
        else:
            self.notify_fallback_once(gh_url)
            candidate_urls = [hf_url]

        for gz_url in candidate_urls:
            try:
                response = requests.get(gz_url, timeout=10)
                response.raise_for_status()
            except Exception:
                if gz_url == gh_url:
                    self.notify_fallback_once(gh_url)
                continue

            try:
                with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
                    data = json.load(f)
                with open(local_path, "w", encoding="utf-8") as out:
                    json.dump(data, out, indent=2)
                return data
            except Exception:
                continue  # decompression, parsing, or local write failed; try the next candidate

        output.add_text(f"D2PFX: Unable to download {filename} from either GitHub or Hugging Face", msg_type="error")
        return None

    def refresh(self):
        self.metadata = self.fetch_gz_json("mods.json.gz", force_refresh=True)
        self.constants = self.fetch_gz_json("constants.json.gz", force_refresh=True)
        self._ensure_release_index(force=True)
        if self.metadata is not None:
            utils.set_state("d2pfx", "last_refresh", int(time.time()))
        return self.metadata is not None

    def _needs_refresh(self):
        if not config.get("d2pfx_auto_refresh_catalogue", True):
            return False
        last_refresh = utils.get_state("d2pfx", "last_refresh", 0)
        return (time.time() - last_refresh) > 21600

    def load(self):
        if self._needs_refresh():
            self.refresh()

        self.metadata = self.fetch_gz_json("mods.json.gz")
        self.constants = self.fetch_gz_json("constants.json.gz")
        return self.metadata is not None

    def get_categories(self):
        if not self.constants:
            return []
        ids = []
        for cat in self.constants.get("categories", []):
            cat_id = cat.get("id") if isinstance(cat, dict) else None
            if not cat_id or cat.get("hidden") or cat_id.lower() in BLACKLIST:
                continue
            ids.append(cat_id)
        return ids

    def _translation(self, key, locale):
        translations = self.constants.get("translations", {})

        localized = translations.get(locale)
        if isinstance(localized, dict) and isinstance(localized.get(key), str):
            return localized[key]

        if isinstance(translations.get(key), str):
            return translations[key]

        if isinstance(self.constants.get(key), str):
            return self.constants[key]

        return None

    def get_category_name(self, cat_id):
        locale = config.get("locale", "en")
        return self._translation(cat_id, locale) or cat_id.capitalize()

    def get_category_description(self, cat_id):
        locale = config.get("locale", "en")
        return self._translation(f"{cat_id}-desc", locale) or ""

    def get_mods(self, cat_id):
        if not self.metadata:
            return []
        data = self.metadata.get("modsData", {}).get(cat_id, [])

        flattened = []

        def _flatten(item):
            if isinstance(item, list):
                for sub in item:
                    _flatten(sub)
            elif isinstance(item, dict):
                if "groups" in item:
                    _flatten(item["groups"])
                elif "mods" in item:
                    _flatten(item["mods"])
                elif "name" in item:  # It's a mod
                    # Extract authors and senders from links
                    links = item.get("links", [])
                    for key, types in [("author", ("author", "modded")), ("sender", ("sender",))]:
                        vals = [l.get("name") or l.get("url") for l in links if l.get("type") in types]
                        vals = [x for x in vals if x]
                        item[key] = vals[0] if len(vals) == 1 else (vals or None)

                    flattened.append(item)
                else:
                    # Check if it's a dict that might contain groups/mods
                    for val in item.values():
                        if isinstance(val, (dict, list)):
                            _flatten(val)

        _flatten(data)
        return flattened

    def get_preview_url(self, cat_id, filename):
        if not filename:
            return None
        return f"{PREVIEWS_URL}{cat_id}/{filename}"

    def get_file_url(self, cat_id, filename):
        return f"{ASSETS_URL}{cat_id}/{filename}"
