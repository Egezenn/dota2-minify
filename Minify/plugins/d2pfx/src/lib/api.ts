import type { D2Mod, InstalledMod } from "./types";

export function getApi() {
  const win = window as any;
  if (win && win.pywebview && win.pywebview.api) {
    return win.pywebview.api;
  }
  if (win && win.parent && win.parent.pywebview && win.parent.pywebview.api) {
    return win.parent.pywebview.api;
  }
  return null;
}

export async function callApi(action: string, params: Record<string, any> = {}): Promise<any> {
  const api = getApi();
  if (!api || !api.call_plugin_api) {
    throw new Error("API not connected");
  }
  const res = await api.call_plugin_api("d2pfx", action, params);
  if (res && typeof res === "object" && res.error) {
    console.error(`D2PFX API Error (${action}):`, res.error);
    throw new Error(String(res.error));
  }
  return res;
}

export function getModKey(m: D2Mod, catId: string): string {
  return `${catId}::${m.name}::${m.label || ""}`;
}

export function isInstalled(m: D2Mod, catId: string, installedList: InstalledMod[]): boolean {
  return installedList.some(
    (inst) =>
      inst.name === m.name &&
      inst.category === catId &&
      (inst.label || "") === (m.label || "")
  );
}

export function notifyParentModsRefreshed() {
  try {
    const parentWin = (window.parent || window) as any;
    if (parentWin) {
      if (typeof parentWin.onModsRefreshed === "function") {
        parentWin.onModsRefreshed();
      }
      parentWin.postMessage({ type: "REFRESH_MODS" }, "*");
    }
  } catch (e) {
    console.error("Error notifying parent of mod refresh:", e);
  }
}
