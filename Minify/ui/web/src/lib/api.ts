import { modsStore } from "./stores/mods";
import { localeStore } from "./stores/locale";

export async function refreshMods() {
  try {
    if (window.pywebview?.api?.get_mods) {
      const mods = await window.pywebview.api.get_mods();
      if (Array.isArray(mods)) modsStore.set(mods);
    }
  } catch (err) {
    console.error("Failed to refresh mods grid:", err);
  }
}

export async function loadApiData(currentLang: string): Promise<{
  isDebugEnv: boolean;
  currentGameLang: string;
  availableUiLangs: string[];
  availableGameLangs: string[];
  logs: any[];
  isPatching: boolean;
  pluginTabs: Array<{ id: string; name: string; entry_point?: string }>;
  pluginContents: Record<string, string>;
}> {
  const api = window.pywebview?.api;
  if (!api) {
    throw new Error("PyWebView API unavailable");
  }

  let isDebugEnv = false;
  let currentGameLang = "english";
  let availableUiLangs: string[] = [];
  let availableGameLangs: string[] = [];
  let logs: any[] = [];
  let isPatching = false;
  let pluginTabs: Array<{ id: string; name: string; entry_point?: string }> = [];
  let pluginContents: Record<string, string> = {};

  if (api.is_debug_env) {
    isDebugEnv = Boolean(await api.is_debug_env());
  }

  const [savedUiLang, savedGameLang, uiLangs, gameLangs] = await Promise.all([
    api.get_current_locale(),
    api.get_current_game_language(),
    api.get_available_languages(),
    api.get_available_game_languages(),
  ]);

  const targetUiLang = savedUiLang || currentLang || "EN";
  currentGameLang = savedGameLang || "english";

  if (Array.isArray(uiLangs) && uiLangs.length > 0) availableUiLangs = uiLangs;
  if (Array.isArray(gameLangs) && gameLangs.length > 0) availableGameLangs = gameLangs;

  const [initialLogs, patchingState, mods, locDict] = await Promise.all([
    api.get_logs(),
    api.is_patching(),
    api.get_mods(),
    api.get_localization(targetUiLang),
  ]);

  if (Array.isArray(initialLogs)) logs = initialLogs;
  isPatching = Boolean(patchingState);
  if (Array.isArray(mods)) modsStore.set(mods);
  if (locDict) localeStore.set({ lang: targetUiLang, dict: locDict });

  if (api.get_plugin_tabs) {
    try {
      const tabs = await api.get_plugin_tabs();
      pluginTabs = tabs || [];
      if (api.get_plugin_content) {
        const contentsMap: Record<string, string> = {};
        for (const p of pluginTabs) {
          try {
            const html = await api.get_plugin_content(p.id);
            if (html) contentsMap[p.id] = html;
          } catch (e) {
            console.error(`Error loading content for plugin ${p.id}:`, e);
          }
        }
        pluginContents = contentsMap;
      }
    } catch (e) {
      console.error("Error loading plugin tabs:", e);
    }
  }

  return {
    isDebugEnv,
    currentGameLang,
    availableUiLangs,
    availableGameLangs,
    logs,
    isPatching,
    pluginTabs,
    pluginContents,
  };
}
