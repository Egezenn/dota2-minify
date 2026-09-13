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

export function injectThemeIntoFrame(frame: HTMLIFrameElement | EventTarget | null | undefined, css?: string) {
  try {
    const el = frame as HTMLIFrameElement | null;
    if (!el?.contentDocument) return;
    const doc = el.contentDocument;
    const themeCss =
      css !== undefined
        ? css
        : (window as any).__lastThemeCss || document.getElementById("minify-theme")?.textContent || "";
    let styleEl = doc.getElementById("minify-theme") as HTMLStyleElement;
    if (!styleEl) {
      styleEl = doc.createElement("style");
      styleEl.id = "minify-theme";
      doc.head.appendChild(styleEl);
    }
    if (styleEl.textContent !== themeCss) {
      styleEl.textContent = themeCss;
    }
    if (doc.body) {
      doc.body.style.backgroundColor = "transparent";
    }
  } catch (e) {
    // ignore
  }
}

export async function applyTheme(themeName?: string): Promise<string> {
  try {
    const api = window.pywebview?.api;
    if (!api) return "";

    let css = "";
    if (api.get_theme_css) {
      css = await api.get_theme_css(themeName);
      (window as any).__lastThemeCss = css;
    }

    if (api.get_theme_url) {
      const themeUrl = await api.get_theme_url(themeName);
      try {
        localStorage.setItem("minify-theme-url", themeUrl);
      } catch (e) {}
      let linkEl = document.getElementById("minify-theme-link") as HTMLLinkElement;
      if (!linkEl) {
        linkEl = document.createElement("link");
        linkEl.id = "minify-theme-link";
        linkEl.rel = "stylesheet";
        document.head.appendChild(linkEl);
      }
      if (linkEl.href !== themeUrl) {
        linkEl.href = themeUrl;
      }
      const oldStyle = document.getElementById("minify-theme");
      if (oldStyle && oldStyle.tagName.toLowerCase() === "style") {
        oldStyle.remove();
      }
    } else if (css) {
      let styleEl = document.getElementById("minify-theme") as HTMLStyleElement;
      if (!styleEl) {
        styleEl = document.createElement("style");
        styleEl.id = "minify-theme";
        document.head.appendChild(styleEl);
      }
      if (styleEl.textContent !== css) {
        styleEl.textContent = css;
      }
    }

    const iframes = document.querySelectorAll<HTMLIFrameElement>("iframe.plugin-frame");
    iframes.forEach((frame) => injectThemeIntoFrame(frame, css));

    return css;
  } catch (err) {
    console.error("Failed to apply theme:", err);
    return "";
  }
}

export async function loadApiData(currentLang: string): Promise<{
  isDebugEnv: boolean;
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
  let logs: any[] = [];
  let isPatching = false;
  let pluginTabs: Array<{ id: string; name: string; entry_point?: string }> = [];
  let pluginContents: Record<string, string> = {};

  if (api.is_debug_env) {
    isDebugEnv = Boolean(await api.is_debug_env());
  }

  const savedUiLang = await api.get_current_locale();
  const targetUiLang = savedUiLang || currentLang || "en";

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
    logs,
    isPatching,
    pluginTabs,
    pluginContents,
  };
}
