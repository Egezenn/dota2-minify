import { derived, writable } from "svelte/store";

interface PluginLocaleState {
  lang: string;
  dict: Record<string, string>;
}

const pluginLocaleStore = writable<PluginLocaleState>({
  lang: "en",
  dict: {},
});

export function setPluginLocale(lang: string, dict: Record<string, string> = {}) {
  pluginLocaleStore.set({ lang, dict });
}

export const t = derived(pluginLocaleStore, ($locale) => {
  return (key: string, args: (string | number)[] = []): string => {
    let text = $locale.dict[key] || key;
    args.forEach((arg, index) => {
      text = text.replace(new RegExp(`\\{${index}\\}`, "g"), String(arg));
    });
    return text;
  };
});
