import { writable } from 'svelte/store';

export interface ModItem {
  name: string;
  enabled: boolean;
  always?: boolean;
  preview?: string | null;
}

export const modsStore = writable<ModItem[]>([]);
