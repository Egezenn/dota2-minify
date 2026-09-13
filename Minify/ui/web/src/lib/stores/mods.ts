import { writable } from 'svelte/store';

export interface ModItem {
  name: string;
  display_name?: string;
  enabled: boolean;
  always?: boolean;
  untickable?: boolean;
  preview?: string | null;
}

export const modsStore = writable<ModItem[]>([]);
