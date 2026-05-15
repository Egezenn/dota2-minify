import gzip
import io
import json
import os

import requests
from core import base, fs

# D2PFX Browser Constants
BASE_URL = "https://raw.githubusercontent.com/h6rd/Dota2PornFxWeb/data/"
ASSETS_URL = "https://raw.githubusercontent.com/h6rd/Dota2PornFxWeb/main/assets/files/"
CACHE_DIR = os.path.join(base.cache_dir, "browsers", "d2pfx")
PREVIEWS_CACHE_DIR = os.path.join(CACHE_DIR, "previews")
BLACKLIST = [
    "guides",
    "item-sounds",
    "news",
    "optimization",
    "tools",
    "sites",
    "packs",
    "huds",  # https://github.com/Egezenn/dota2-minify/issues/143
    "fonts",  # https://github.com/Egezenn/dota2-minify/issues/136
]


class DataManager:
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.previews_dir = PREVIEWS_CACHE_DIR
        fs.create_dirs(self.cache_dir, self.previews_dir)
        self.metadata = {}
        self.constants = {}

    def download_file(self, url, dest, progress_tag=None):
        return fs.download_file(url, dest, progress_tag=progress_tag)

    def fetch_gz_json(self, filename, force_refresh=False):
        local_path = os.path.join(self.cache_dir, filename.replace(".gz", ""))
        gz_url = f"{BASE_URL}data/{filename}"

        if not force_refresh and os.path.exists(local_path):
            try:
                with open(local_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        try:
            response = requests.get(gz_url, timeout=10)
            if response.status_code == 200:
                with gzip.GzipFile(fileobj=io.BytesIO(response.content)) as f:
                    data = json.load(f)
                    with open(local_path, "w", encoding="utf-8") as out:
                        json.dump(data, out, indent=2)
                    return data
        except Exception as e:
            print(f"Error fetching {filename}: {e}")

        return None

    def refresh(self):
        self.metadata = self.fetch_gz_json("mods.json.gz", force_refresh=True)
        self.constants = self.fetch_gz_json("constants.json.gz", force_refresh=True)
        return self.metadata is not None

    def load(self):
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
                    # Extract author from links
                    for link in item.get("links", []):
                        if link.get("type") == "author":
                            item["author"] = link.get("url")
                            break
                    flattened.append(item)
                else:
                    # Check if it's a dict that might contain groups/mods
                    for val in item.values():
                        if isinstance(val, (dict, list)):
                            _flatten(val)

        _flatten(data)
        return flattened

    def get_preview_url(self, cat_id, filename):
        if filename and filename.endswith(".webp"):
            filename = filename.replace(".webp", ".jpg")
        return f"{BASE_URL}previews/{cat_id}/{filename}"

    def get_file_url(self, cat_id, filename):
        return f"{ASSETS_URL}{cat_id}/{filename}"
