export interface Category {
  id: string;
  name: string;
  description: string;
}

export interface D2Mod {
  name: string;
  label?: string;
  author?: string | string[];
  sender?: string | string[];
  tags?: string[] | Record<string, boolean>;
  preview_url?: string | null;
  file?: string;
  links?: any[];
  [key: string]: any;
}

export interface InstalledMod {
  name: string;
  category: string;
  label?: string;
  folder: string;
}
