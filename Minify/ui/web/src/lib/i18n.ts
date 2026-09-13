import { derived } from "svelte/store";
import { localeStore } from "./stores/locale";

/**
 * Reactive derived store for localized text.
 * Automatically updates all subscribing Svelte components when localeStore changes.
 *
 * Example:
 *   {$t('button_close')}
 *   {$t('status_download_failed', [err])}
 */
export const t = derived(localeStore, ($locale) => {
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
