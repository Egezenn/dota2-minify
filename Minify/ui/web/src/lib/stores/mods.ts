import { writable } from 'svelte/store';

export interface ModItem {
  name: string;
  enabled: boolean;
  always?: boolean;
}

export const modsStore = writable<ModItem[]>([]);
