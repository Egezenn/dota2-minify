import type { UpdateInfo } from "./types";

export const GITHUB_RELEASES_URL = "https://api.github.com/repos/Egezenn/dota2-minify/releases";

export async function getAppVersion(): Promise<string | null> {
  try {
    if (window.pywebview?.api?.get_version) {
      const ver = await window.pywebview.api.get_version();
      if (ver && typeof ver === "string" && ver.trim().length > 0) {
        return ver.trim();
      }
    }
  } catch (e) {
    console.error("Failed to get version from API:", e);
  }
  return null;
}

export function cleanVersion(v: string): string {
  if (!v) return "";
  return v.replace(/^(v|minify-?)/i, "").trim();
}

export function compareVersions(v1: string, v2: string): number {
  const s1 = cleanVersion(v1);
  const s2 = cleanVersion(v2);

  const parse = (str: string) => {
    const [main, ...preParts] = str.split("-");
    const pre = preParts.join("-");
    const nums = main.split(".").map((n) => parseInt(n, 10) || 0);
    return { nums, pre };
  };

  const p1 = parse(s1);
  const p2 = parse(s2);

  const len = Math.max(p1.nums.length, p2.nums.length);
  for (let i = 0; i < len; i++) {
    const n1 = p1.nums[i] || 0;
    const n2 = p2.nums[i] || 0;
    if (n1 > n2) return 1;
    if (n1 < n2) return -1;
  }

  if (!p1.pre && p2.pre) return 1;
  if (p1.pre && !p2.pre) return -1;
  if (p1.pre && p2.pre) return p1.pre.localeCompare(p2.pre);

  return 0;
}

export async function getIgnoredUpdate(): Promise<string | null> {
  try {
    const val = await window.pywebview?.api?.get_state?.("ignored_update");
    return typeof val === "string" && val.trim().length > 0 ? val.trim() : null;
  } catch (e) {
    console.error("Failed to read ignored update from states.json:", e);
    return null;
  }
}

export async function ignoreUpdate(version: string): Promise<void> {
  const cleaned = cleanVersion(version);
  try {
    await window.pywebview?.api?.set_state?.("ignored_update", cleaned);
  } catch (e) {
    console.error("Failed to save ignored update to states.json:", e);
  }
}

export async function checkForUpdates(options: {
  currentVersion?: string | null;
  optIntoRcs?: boolean;
  force?: boolean;
} = {}): Promise<UpdateInfo | null> {
  const current = options.currentVersion !== undefined ? options.currentVersion : await getAppVersion();
  if (!current) {
    return null;
  }

  const optIntoRcs = Boolean(options.optIntoRcs);
  const force = Boolean(options.force);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 4000);

  try {
    const res = await fetch(GITHUB_RELEASES_URL, {
      signal: controller.signal,
      headers: { Accept: "application/vnd.github.v3+json" },
    });
    clearTimeout(timeoutId);
    if (!res.ok) return null;

    const releases = await res.json();
    if (!Array.isArray(releases) || releases.length === 0) return null;

    const ignored = await getIgnoredUpdate();

    for (const rel of releases) {
      if (!rel || typeof rel !== "object") continue;
      const tag = String(rel.tag_name || "").trim();
      const remoteVer = cleanVersion(tag);
      if (!remoteVer) continue;

      const isPre = Boolean(rel.prerelease);
      const currentIsPre = current.toLowerCase().includes("rc");
      if (isPre && !optIntoRcs && !currentIsPre) {
        continue;
      }

      if (compareVersions(remoteVer, current) > 0) {
        if (!force && ignored && ignored === remoteVer) {
          return null;
        }

        let downloadUrl = "";
        if (Array.isArray(rel.assets)) {
          const exeAsset = rel.assets.find((a: any) => typeof a.name === "string" && a.name.toLowerCase().endsWith(".exe"));
          const zipAsset = rel.assets.find((a: any) => typeof a.name === "string" && a.name.toLowerCase().endsWith(".zip"));
          const chosen = exeAsset || zipAsset || rel.assets[0];
          if (chosen?.browser_download_url) {
            downloadUrl = chosen.browser_download_url;
          }
        }

        return {
          version: remoteVer,
          currentVersion: current,
          title: rel.name || `Release v${remoteVer}`,
          body: rel.body || "",
          releaseUrl: rel.html_url || `https://github.com/Egezenn/dota2-minify/releases/tag/${tag}`,
          downloadUrl: downloadUrl || rel.html_url,
          isPrerelease: isPre,
          publishedAt: rel.published_at,
        };
      }
    }

    return null;
  } catch {
    clearTimeout(timeoutId);
    return null;
  }
}
