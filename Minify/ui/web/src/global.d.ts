export {};

declare global {
  interface Window {
    pywebview?: {
      api: {
        get_current_locale: () => Promise<string>;
        get_current_game_language: () => Promise<string>;
        get_available_languages: () => Promise<string[]>;
        get_available_game_languages: () => Promise<string[]>;
        get_logs: () => Promise<
          Array<{ text: string; type: string; timestamp?: string }>
        >;
        is_patching: () => Promise<boolean>;
        is_debug_env: () => Promise<boolean>;
        get_mods: () => Promise<Array<{ name: string; enabled: boolean }>>;
        get_mod_details: (
          modName: string,
          lang?: string,
        ) => Promise<{
          name: string;
          notes: string | null;
          preview: string | null;
          has_notes: boolean;
          has_preview: boolean;
        }>;
        get_localization: (lang: string) => Promise<Record<string, string>>;
        set_locale: (lang: string) => Promise<boolean>;
        set_game_language: (lang: string) => Promise<boolean>;
        set_mods: (data: Record<string, boolean>) => Promise<boolean>;
        start_patch: () => Promise<{ status: string }>;
        clear_logs: () => Promise<boolean>;
        get_settings: () => Promise<{
          schema: Array<{
            key: string;
            text: string;
            default: boolean;
            type: string;
          }>;
          values: Record<string, boolean>;
        }>;
        set_setting: (key: string, value: any) => Promise<boolean>;
      };
    };
    onLogReceived?: (logEntry: {
      text: string;
      type: string;
      timestamp?: string;
    }) => void;
    onPatchStatusChange?: (status: boolean) => void;
  }
}
