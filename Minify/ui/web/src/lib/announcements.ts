import type { Announcement } from "./types";

export const ANNOUNCEMENTS_URL = "https://egezenn.github.io/dota2-minify/announcements.json";
export const STATE_KEY = "announcements_seen";

export function getAnnouncementId(ann: Announcement): string {
  if (!ann || !ann.time) return "";
  return ann.time.replace(/[-+]/g, "").split("=")[0].trim();
}

export function parseTimeCondition(timeStr: string): boolean {
  if (!timeStr) return false;
  const now = Math.floor(Date.now() / 1000);

  try {
    if (timeStr.includes("-")) {
      const ts = parseInt(timeStr.replace("-", "").trim(), 10);
      return !isNaN(ts) && now <= ts;
    } else if (timeStr.includes("+")) {
      const ts = parseInt(timeStr.replace("+", "").trim(), 10);
      return !isNaN(ts) && now >= ts;
    } else if (timeStr.includes("=")) {
      const parts = timeStr.split("=");
      if (parts.length === 2) {
        const t1 = parseInt(parts[0].trim(), 10);
        const t2 = parseInt(parts[1].trim(), 10);
        return !isNaN(t1) && !isNaN(t2) && now >= t1 && now <= t2;
      }
    }
    return true;
  } catch {
    return false;
  }
}

export function checkVersion(versions?: string[] | string, currentVersion?: string): boolean {
  if (!versions || (Array.isArray(versions) && versions.length === 0)) {
    return true;
  }
  if (!currentVersion) return true;

  const allowed: string[] = Array.isArray(versions)
    ? versions.map((v) => String(v).trim())
    : versions.split(",").map((v) => v.trim());

  return allowed.some((v) => currentVersion === v || currentVersion.startsWith(v));
}

export async function getSeenAnnouncements(): Promise<string[]> {
  try {
    const seen = await window.pywebview?.api?.get_state?.(STATE_KEY);
    return Array.isArray(seen) ? seen : [];
  } catch (e) {
    console.error("Failed to read seen announcements from states.json:", e);
    return [];
  }
}

export async function markAnnouncementSeen(id: string): Promise<void> {
  if (!id) return;
  try {
    const seen = await getSeenAnnouncements();
    if (!seen.includes(id)) {
      seen.push(id);
      await window.pywebview?.api?.set_state?.(STATE_KEY, seen);
    }
  } catch (e) {
    console.error("Failed to mark announcement seen:", e);
  }
}

export async function fetchPendingAnnouncements(currentVersion?: string): Promise<Announcement[]> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 4000);

  try {
    const res = await fetch(ANNOUNCEMENTS_URL, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    clearTimeout(timeoutId);
    if (!res.ok) return [];

    const data = await res.json();
    if (!Array.isArray(data)) return [];

    const seen = await getSeenAnnouncements();
    return data.filter((ann: Announcement) => {
      if (!ann || typeof ann !== "object") return false;
      if (!ann.time || !ann.text) return false;

      const id = getAnnouncementId(ann);
      if (!id || seen.includes(id)) return false;

      if (!parseTimeCondition(ann.time)) return false;
      if (!checkVersion(ann.versions, currentVersion)) return false;

      return true;
    });
  } catch {
    clearTimeout(timeoutId);
    return [];
  }
}
