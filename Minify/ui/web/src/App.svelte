<script lang="ts">
  import { onMount } from "svelte";
  import { modsStore } from "./lib/stores/mods";
  import { localeStore } from "./lib/stores/locale";
  import { loadApiData, refreshMods } from "./lib/api";
  import Header from "./lib/components/Header.svelte";
  import ModGrid from "./lib/components/ModGrid.svelte";
  import Terminal from "./lib/components/Terminal.svelte";
  import Settings from "./lib/components/Settings.svelte";
  import type { DownloadItem } from "./lib/types";
  import DownloadNotification from "./lib/components/DownloadNotification.svelte";

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
  let isDebugEnv = false;

  $: dict = $localeStore.dict;
  $: currentLang = $localeStore.lang;

  async function handleLoadApiData() {
    if (initialized) return;
    try {
      const data = await loadApiData(currentLang);
      initialized = true;
      isDebugEnv = data.isDebugEnv;
      currentGameLang = data.currentGameLang;
      availableUiLangs = data.availableUiLangs;
      availableGameLangs = data.availableGameLangs;
      logs = data.logs;
      isPatching = data.isPatching;
      pluginTabs = data.pluginTabs;
      pluginContents = data.pluginContents;
    } catch (err) {
      console.error("Error initializing PyWebView API:", err);
    }
  }

  async function initPyWebView() {
    if (window.pywebview?.api) {
      await handleLoadApiData();
      return;
    }
    window.addEventListener("pywebviewready", handleLoadApiData, { once: true });
  }

  onMount(() => {
    const handleContextMenu = (e: MouseEvent) => {
      if (!isDebugEnv) {
        e.preventDefault();
      }
    };

    const handleWindowMessage = (e: MessageEvent) => {
      if (e.data?.type === "REFRESH_MODS") {
        refreshMods();
      }
    };

    window.addEventListener("contextmenu", handleContextMenu);
    window.addEventListener("message", handleWindowMessage);

    (window as any).onModsRefreshed = refreshMods;

    window.onLogReceived = (logEntry: {
      text: string;
      type: string;
      timestamp?: string;
    }) => {
      const formattedMsg = `[${logEntry.timestamp || ""}] ${logEntry.text}`;
      if (logEntry.type === "error") {
        console.error(formattedMsg);
      } else if (logEntry.type === "warning") {
        console.warn(formattedMsg);
      } else {
        console.log(formattedMsg);
      }
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
      window.removeEventListener("message", handleWindowMessage);
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
    }
  }

  async function handleLanguageChange(lang: string) {
    const api = window.pywebview?.api;
    if (!api) return;
    try {
      await api.set_locale(lang);
      const dict = await api.get_localization(lang);
      if (dict) {
        localeStore.set({ lang, dict });
      }
    } catch (err) {
      console.error("Error setting language:", err);
    }
  }

  async function handleGameLanguageChange(lang: string) {
    const api = window.pywebview?.api;
    if (!api) return;
    try {
      await api.set_game_language(lang);
      currentGameLang = lang;
    } catch (err) {
      console.error("Error setting game language:", err);
    }
  }
  function handleGameLangSelect(e: Event) {
    const target = e.target as HTMLSelectElement;
    if (target) {
      handleGameLanguageChange(target.value);
    }
  }
</script>

<div class="app-container">
  <Header
    {activeTab}
    {currentGameLang}
    {availableGameLangs}
    {isPatching}
    {pluginTabs}
    onTabChange={(tab) => (activeTab = tab)}
    onGameLangChange={handleGameLangSelect}
    onPatch={handlePatch}
  />

  <main class="content-area">
    <div class="tab-pane" class:hidden={activeTab !== "mods"}>
      <ModGrid />
    </div>

    <div class="tab-pane" class:hidden={activeTab !== "terminal"}>
      <Terminal
        {logs}
        bind:autoScroll
        onClear={() => {
          logs = [];
          window.pywebview?.api?.clear_logs();
        }}
      />
    </div>

    <div class="tab-pane" class:hidden={activeTab !== "settings"}>
      <Settings />
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
  </main>

  <div class="download-stack">
    <DownloadNotification
      {downloads}
      onDismiss={handleDismissDownload}
    />
  </div>
</div>

<style>
  :global(*),
  :global(*::before),
  :global(*::after) {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    border-radius: 0 !important;
    box-shadow: none !important;
    transition: none !important;
    animation: none !important;
  }

  :global(body),
  :global(html) {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #000;
    background: #fff;
    overflow: hidden;
  }

  .app-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    background: #fff;
    color: #000;
    position: relative;
  }

  .content-area {
    flex: 1;
    overflow: hidden;
    position: relative;
  }

  .tab-pane {
    height: 100%;
    width: 100%;
  }

  .tab-pane.hidden {
    display: none;
  }

  .plugin-frame {
    width: 100%;
    height: 100%;
    border: none;
  }

  .download-stack {
    position: fixed;
    bottom: 12px;
    right: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 9999;
  }
</style>
