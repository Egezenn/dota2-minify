import gzip
import io
import json
import os
import time

import requests
from core import base, config, fs, output, utils

# D2PFX Browser Constants
BASE_URL = "https://raw.githubusercontent.com/h6rd/Dota2PornFxWeb/data/"
ASSETS_URL = "https://raw.githubusercontent.com/h6rd/Dota2PornFxWeb/main/assets/files/"
PREVIEWS_URL = "https://raw.githubusercontent.com/h6rd/Dota2PornFxWeb/main/assets/previews/"

# Hugging Face fallback
HF_BASE_URL = "https://huggingface.co/datasets/hrdq/Dota2PornFx/resolve/main/compressed/"
HF_ASSETS_URL = "https://huggingface.co/datasets/hrdq/Dota2PornFx/resolve/main/assets/files/"
HF_PREVIEWS_URL = "https://huggingface.co/datasets/hrdq/Dota2PornFx/resolve/main/assets/previews/"

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
    "huds",  # https://github.com/Egezenn/dota2-minify/issues/143
    "fonts",
]


class DataManager:
    HOST_REACHABLE_CACHE = {}
    REACHABILITY_TTL = 60
    NOTIFIED_HOSTS = set()

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

    @classmethod
    def is_url_reachable(cls, url, timeout=3):
        from urllib.parse import urlparse

        host = urlparse(url).netloc
        cached = cls.HOST_REACHABLE_CACHE.get(host)
        now = time.time()
        if cached and (now - cached[1]) < cls.REACHABILITY_TTL:
            return cached[0]

        try:
            requests.head(url, timeout=timeout, allow_redirects=True)
            reachable = True
        except Exception:
            reachable = False

        cls.HOST_REACHABLE_CACHE[host] = (reachable, now)
        return reachable

    @classmethod
    def notify_fallback_once(cls, gh_url):
        from urllib.parse import urlparse

        host = urlparse(gh_url).netloc
        if host in cls.NOTIFIED_HOSTS:
            return
        cls.NOTIFIED_HOSTS.add(host)
        try:
            output.add_text(f"{host} unreachable, D2PFX is using the Hugging Face mirror", msg_type="info")
        except Exception:
            print(f"{host} unreachable, D2PFX is using the Hugging Face mirror")

    def download_file(self, url, dest, progress_tag=None, name=None, emit_progress=True, fallback_url=None):
        fallback_url = fallback_url or self.to_hf_fallback(url)

        if fallback_url and fallback_url != url and not self.is_url_reachable(url):
            self.notify_fallback_once(url)
            return fs.download_file(
                fallback_url, dest, progress_tag=progress_tag, name=name, emit_progress=emit_progress
            )

        success = fs.download_file(url, dest, progress_tag=progress_tag, name=name, emit_progress=emit_progress)
        if not success and fallback_url and fallback_url != url:
            self.notify_fallback_once(url)
            success = fs.download_file(
                fallback_url, dest, progress_tag=progress_tag, name=name, emit_progress=emit_progress
            )
        return success

    def fetch_gz_json(self, filename, force_refresh=False):
        local_path = os.path.join(self.cache_dir, filename.replace(".gz", ""))
        gh_url = f"{BASE_URL}data/{filename}"
        hf_url = f"{HF_BASE_URL}data/{filename}"

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
                if response.status_code == 200:
                    with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
                        data = json.load(f)
                        with open(local_path, "w", encoding="utf-8") as out:
                            json.dump(data, out, indent=2)
                        return data
            except Exception:
                continue  # try the next candidate silently

        print(f"D2PFX: Unable to download {filename} from either GitHub or Hugging Face")
        return None

    def refresh(self):
        self.metadata = self.fetch_gz_json("mods.json.gz", force_refresh=True)
        self.constants = self.fetch_gz_json("constants.json.gz", force_refresh=True)
        if self.metadata is not None:
            utils.set_state("d2pfx", "last_refresh", int(time.time()))
        return self.metadata is not None

    def _needs_refresh(self):
        if not config.get("d2pfx_auto_refresh_catalogue", True):
            return False
        last_refresh = utils.get_state("d2pfx", "last_refresh", 0)
        return (time.time() - last_refresh) > 86400

    def load(self):
        if self._needs_refresh():
            self.refresh()

        self.metadata = self.fetch_gz_json("mods.json.gz")
        self.constants = self.fetch_gz_json("constants.json.gz")
        return self.metadata is not None

    def get_categories(self):
        if not self.metadata:
            return []
        mods_data = self.metadata.get("modsData", {})
        return sorted([c for c in mods_data.keys() if c.lower() not in BLACKLIST])

    def get_category_name(self, cat_id):
        if not self.constants:
            return cat_id.capitalize()
        return self.constants.get(cat_id, cat_id.capitalize())

    def get_category_description(self, cat_id):
        if not self.constants:
            return ""
        return self.constants.get(f"{cat_id}-desc", "")

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
