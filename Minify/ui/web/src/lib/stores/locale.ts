import { writable } from 'svelte/store';

export interface LocaleState {
  lang: string;
  dict: Record<string, string>;
}

export const localeStore = writable<LocaleState>({
  lang: 'EN',
  dict: {},
});
