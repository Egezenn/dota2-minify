/// <reference types="vite/client" />

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
        get_version: () => Promise<string>;
        perform_update: (url: string) => Promise<boolean>;
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
          methods?: Array<{
            name: string;
            type: "tree" | "json" | "blacklist" | "css" | "python" | "xml" | "text";
            content?: string;
            tree?: any;
            badge?: string;
          }>;
        }>;
        get_localization: (lang: string) => Promise<Record<string, string>>;
        set_locale: (lang: string) => Promise<boolean>;
        set_game_language: (lang: string) => Promise<boolean>;
        set_mods: (data: Record<string, boolean>) => Promise<boolean>;
        start_patch: () => Promise<{ status: string }>;
        start_uninstall: (remove_everything?: boolean) => Promise<{ status: string }>;
        clear_logs: () => Promise<boolean>;
        get_steam_accounts: () => Promise<
          Array<{ id: string; name: string; account_name?: string; timestamp?: number }>
        >;
        get_settings: () => Promise<{
          schema: Array<{
            key: string;
            text: string;
            type: string;
            default?: any;
            mod?: string | null;
            force?: boolean;
            items?: Array<string | { value: string; label: string }>;
            var_type?: "int" | "float";
            step?: number;
            min?: number;
            max?: number;
          }>;
          values: Record<string, any>;
        }>;
        set_setting: (key: string, value: any, mod_name?: string) => Promise<boolean>;
        run_mod_function: (mod_name: string, function_name: string) => Promise<boolean>;
        reset_native_settings: () => Promise<boolean>;
        reset_mod_settings: (mod_name: string) => Promise<boolean>;
        get_available_themes?: () => Promise<Array<{ value: string; label: string }>>;
        get_theme_url?: (theme_name?: string) => Promise<string>;
        get_theme_css?: (theme_name?: string) => Promise<string>;
        get_state?: (key: string, defaultValue?: any) => Promise<any>;
        set_state?: (key: string, value: any) => Promise<boolean>;
        check_workshop_tools_needed?: () => Promise<boolean>;
        extract_workshop_tools?: () => Promise<boolean>;
        get_plugin_tabs?: () => Promise<Array<{ id: string; name: string; icon?: string; entry_point?: string }>>;
        get_plugin_content?: (plugin_id: string) => Promise<string>;
        call_plugin_api?: (plugin_id: string, action: string, params?: Record<string, any>) => Promise<any>;
      };
    };
    onLogReceived?: (logEntry: {
      text: string;
      type: string;
      timestamp?: string;
    }) => void;
    onPatchStatusChange?: (status: boolean) => void;
    onDownloadProgress?: (data: {
      id: string;
      name: string;
      downloaded_bytes: number;
      total_bytes: number;
      status: "downloading" | "finished" | "error";
      error?: string;
    }) => void;
  }
}
