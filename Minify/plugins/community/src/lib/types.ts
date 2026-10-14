export interface RegistryEntry {
  id: string;
  name: string;
  type: "mod" | "plugin" | "theme";
  repo: string;
  preview: string;
  notes_url: string;
  installed: boolean;
  installed_tag: string | null;
  installed_compatible: boolean;
  current_version: string;
  latest_tag: string | null;
  update_available: boolean;
  available: boolean;
  error: string | null;
}
