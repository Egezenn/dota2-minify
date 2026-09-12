import { writable, derived } from "svelte/store";

export interface PluginLocaleState {
  lang: string;
  dict: Record<string, string>;
}

export const pluginLocaleStore = writable<PluginLocaleState>({
  lang: "en",
  dict: {},
});

export function setPluginLocale(lang: string, dict: Record<string, string> = {}) {
  pluginLocaleStore.set({ lang, dict });
}

export const t = derived(pluginLocaleStore, ($locale) => {
  return (key: string, args?: (string | number)[]): string => {
    if (!key) return "";
    const cleanKey = key.startsWith("&") ? key.slice(1) : key;
    let text = $locale.dict && cleanKey in $locale.dict ? $locale.dict[cleanKey] : cleanKey;
    if (args && args.length > 0) {
      args.forEach((arg, index) => {
        text = text.replace(new RegExp(`\\{${index}\\}`, "g"), String(arg));
      });
    }
    return text;
  };
});
