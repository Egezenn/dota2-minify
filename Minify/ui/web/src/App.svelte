<script lang="ts">
  import { onMount } from "svelte";
  import { modsStore } from "./lib/stores/mods";
  import { localeStore } from "./lib/stores/locale";
  import Header from "./lib/components/Header.svelte";
  import ModGrid from "./lib/components/ModGrid.svelte";
  import Terminal from "./lib/components/Terminal.svelte";
  import Settings from "./lib/components/Settings.svelte";
  import DownloadNotification, { type DownloadItem } from "./lib/components/DownloadNotification.svelte";

  let activeTab: string = "mods";
  let pluginTabs: Array<{ id: string; name: string; entry_point?: string }> = [];

  let pluginContents: Record<string, string> = {};
  let downloads: DownloadItem[] = [];
  let logs: Array<{ text: string; type: string; timestamp?: string }> = [];
  let isPatching = false;
  let autoScroll = true;

  let availableUiLangs: string[] = [];
  let availableGameLangs: string[] = [];
  let currentGameLang = "english";
  let initialized = false;

  $: dict = $localeStore.dict;
  $: currentLang = $localeStore.lang;

  let isDebugEnv = false;

  async function loadApiData() {
    if (initialized) return;
    const api = window.pywebview?.api;
    if (!api) return;

    initialized = true;
    try {
      if (api.is_debug_env) {
        isDebugEnv = Boolean(await api.is_debug_env());
      }

      // 1. Core featureset loading first
      const [savedUiLang, savedGameLang, uiLangs, gameLangs] =
        await Promise.all([
          api.get_current_locale(),
          api.get_current_game_language(),
          api.get_available_languages(),
          api.get_available_game_languages(),
        ]);

      const targetUiLang = savedUiLang || currentLang || "EN";
      currentGameLang = savedGameLang || "english";
      if (Array.isArray(uiLangs) && uiLangs.length > 0)
        availableUiLangs = uiLangs;
      if (Array.isArray(gameLangs) && gameLangs.length > 0)
        availableGameLangs = gameLangs;

      const [initialLogs, patchingState, mods, locDict] = await Promise.all([
        api.get_logs(),
        api.is_patching(),
        api.get_mods(),
        api.get_localization(targetUiLang),
      ]);

      if (Array.isArray(initialLogs)) logs = initialLogs;
      isPatching = Boolean(patchingState);
      if (Array.isArray(mods)) modsStore.set(mods);
      if (locDict) localeStore.set({ lang: targetUiLang, dict: locDict });

      // 2. Plugins loaded asynchronously in the background
      if (api.get_plugin_tabs) {
        api.get_plugin_tabs().then(async (tabs) => {
          pluginTabs = tabs || [];
          if (api.get_plugin_content) {
            const contentsMap: Record<string, string> = {};
            for (const p of pluginTabs) {
              try {
                const html = await api.get_plugin_content(p.id);
                if (html) {
                  contentsMap[p.id] = html;
                }
              } catch (e) {
                console.error(`Error loading content for plugin ${p.id}:`, e);
              }
            }
            pluginContents = contentsMap;
          }
        }).catch((e) => {
          console.error("Error loading plugin tabs:", e);
        });
      }
    } catch (err) {
      console.error("Error initializing PyWebView API:", err);
    }
  }


  async function initPyWebView() {
    if (window.pywebview?.api) {
      await loadApiData();
      return;
    }

    window.addEventListener("pywebviewready", loadApiData, { once: true });
  }

  onMount(() => {
    const handleContextMenu = (e: MouseEvent) => {
      if (!isDebugEnv) {
        e.preventDefault();
      }
    };

    window.addEventListener("contextmenu", handleContextMenu);

    window.onLogReceived = (logEntry: {
      text: string;
      type: string;
      timestamp?: string;
    }) => {
      logs = [...logs, logEntry];
    };

    window.onPatchStatusChange = (status: boolean) => {
      isPatching = status;
    };

    window.onDownloadProgress = (data: DownloadItem) => {
      const idx = downloads.findIndex((d) => d.id === data.id);
      if (idx !== -1) {
        downloads[idx] = { ...data };
        downloads = [...downloads];
      } else {
        downloads = [...downloads, data];
      }

      if (data.status === "finished" || data.status === "error") {
        setTimeout(() => {
          handleDismissDownload(data.id);
        }, 3500);
      }
    };

    initPyWebView();

    return () => {
      window.removeEventListener("contextmenu", handleContextMenu);
    };
  });

  function handleDismissDownload(id: string) {
    downloads = downloads.filter((d) => d.id !== id);
  }

  function getCurrentTime() {
    const now = new Date();
    return now.toTimeString().split(" ")[0];
  }

  async function handlePatch() {
    if (isPatching) return;

    isPatching = true;
    activeTab = "terminal";
    try {
      await window.pywebview?.api?.start_patch();
    } catch (err) {
      logs = [
        ...logs,
        {
          text: `Error triggering patch: ${err}`,
          type: "error",
          timestamp: getCurrentTime(),
        },
      ];
      isPatching = false;
    }
  }

  async function handleSaveMods(data: Record<string, boolean>) {
    try {
      await window.pywebview?.api?.set_mods(data);
    } catch (err) {
      console.error("Failed to save mods state:", err);
    }
  }

  async function handleGameLangChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const newGameLang = target.value;
    currentGameLang = newGameLang;
    try {
      await window.pywebview?.api?.set_game_language(newGameLang);
    } catch (err) {
      console.error("Failed to set game language:", err);
    }
  }

  async function handleClear() {
    logs = [];
    try {
      await window.pywebview?.api?.clear_logs();
    } catch (err) {
      console.error("Failed to clear logs:", err);
    }
  }

  async function handleSettingChange(key: string, value: boolean) {
    try {
      await window.pywebview?.api?.set_setting(key, value);
    } catch (err) {
      console.error("Failed to save setting:", err);
    }
  }
</script>

<main class="app-container">
  <Header
    {activeTab}
    {currentGameLang}
    {availableGameLangs}
    {isPatching}
    {pluginTabs}
    onTabChange={(tab) => (activeTab = tab)}
    onGameLangChange={handleGameLangChange}
    onPatch={handlePatch}
  />

  <section class="main-content">
    <div class="tab-pane" class:hidden={activeTab !== "mods"}>
      <ModGrid onSaveMods={handleSaveMods} />
    </div>
    <div class="tab-pane" class:hidden={activeTab !== "terminal"}>
      <Terminal {logs} bind:autoScroll onClear={handleClear} />
    </div>
    <div class="tab-pane" class:hidden={activeTab !== "settings"}>
      <Settings active={activeTab === "settings"} onSettingChange={handleSettingChange} />
    </div>
    {#each pluginTabs as plugin}
      <div class="tab-pane" class:hidden={activeTab !== plugin.id}>
        {#if pluginContents[plugin.id]}
          <iframe
            srcdoc={pluginContents[plugin.id]}
            title={plugin.name}
            class="plugin-frame"
          ></iframe>
        {:else if plugin.entry_point && !plugin.entry_point.startsWith("file://")}
          <iframe
            src={plugin.entry_point}
            title={plugin.name}
            class="plugin-frame"
          ></iframe>
        {/if}
      </div>
    {/each}
  </section>

  <DownloadNotification {downloads} onDismiss={handleDismissDownload} />
</main>

<style>
  .app-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    padding: 8px;
    gap: 8px;
  }

  .main-content {
    flex: 1;
    border: 1px solid #ccc;
    overflow: hidden;
    background: #fff;
  }

  .tab-pane {
    width: 100%;
    height: 100%;
  }

  .tab-pane.hidden {
    display: none !important;
  }

  .plugin-frame {
    width: 100%;
    height: 100%;
    border: none;
    background: #fff;
  }
</style>
