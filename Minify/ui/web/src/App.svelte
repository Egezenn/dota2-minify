<script lang="ts">
  import { onMount } from "svelte";
  import { modsStore } from "./lib/stores/mods";
  import { localeStore } from "./lib/stores/locale";
  import { loadApiData, refreshMods, applyTheme, injectThemeIntoFrame } from "./lib/api";
  import Header from "./lib/components/Header.svelte";
  import ModGrid from "./lib/components/ModGrid.svelte";
  import Terminal from "./lib/components/Terminal.svelte";
  import Settings from "./lib/components/Settings.svelte";
  import type { DownloadItem, Announcement, UpdateInfo } from "./lib/types";
  import DownloadNotification from "./lib/components/DownloadNotification.svelte";
  import UninstallModal from "./lib/components/UninstallModal.svelte";
  import AnnouncementModal from "./lib/components/AnnouncementModal.svelte";
  import UpdateModal from "./lib/components/UpdateModal.svelte";
  import WorkshopToolsDetectedModal from "./lib/components/WorkshopToolsDetectedModal.svelte";
  import WorkshopDownloadModal from "./lib/components/WorkshopDownloadModal.svelte";
  import { fetchPendingAnnouncements, markAnnouncementSeen } from "./lib/announcements";
  import { checkForUpdates, ignoreUpdate, getAppVersion } from "./lib/updater";

  let activeTab: string = "mods";
  let pluginTabs: Array<{ id: string; name: string; entry_point?: string }> = [];
  let pluginContents: Record<string, string> = {};

  let downloads: DownloadItem[] = [];
  let logs: Array<{ text: string; type: string; timestamp?: string }> = [];
  let isPatching = false;
  let autoScroll = true;
  let showUninstallModal = false;
  let pendingAnnouncements: Announcement[] = [];
  let showAnnouncementModal = false;
  let pendingUpdate: UpdateInfo | null = null;
  let showUpdateModal = false;
  let showWorkshopModal = false;
  let showWorkshopDownloadModal = false;

  let initialized = false;
  let isDebugEnv = false;

  $: currentLang = $localeStore.lang;

  async function handleLoadApiData() {
    if (initialized) return;
    try {
      const data = await loadApiData(currentLang);
      initialized = true;
      isDebugEnv = data.isDebugEnv;
      logs = data.logs;
      isPatching = data.isPatching;
      pluginTabs = data.pluginTabs;
      pluginContents = data.pluginContents;
    } catch (err) {
      console.error("Error initializing PyWebView API:", err);
    }
  }

  async function initTheme() {
    try {
      const api = window.pywebview?.api;
      const themeInit = await api?.get_state?.("system_theme_init");
      if (!themeInit) {
        const prefersDark =
          typeof window !== "undefined" &&
          window.matchMedia &&
          window.matchMedia("(prefers-color-scheme: dark)").matches;
        const initialTheme = prefersDark ? "dark" : "light";
        if (api?.set_setting) {
          await api.set_setting("theme", initialTheme);
        }
        await api?.set_state?.("system_theme_init", true);
        await applyTheme(initialTheme);
        return;
      }
      await applyTheme();
    } catch (err) {
      console.error("Error initializing theme:", err);
    }
  }

  function dismissLoader() {
    const loader = document.getElementById("loading-screen");
    if (loader) {
      loader.classList.add("fade-out");
      setTimeout(() => loader.remove(), 250);
    }
    document.body.classList.add("loaded");
  }

  async function initPyWebView() {
    const run = async () => {
      try {
        await Promise.all([initTheme(), handleLoadApiData()]);
      } finally {
        dismissLoader();
        getAppVersion().then(async (appVersion) => {
          let announcementsShown = false;
          try {
            const announcements = await fetchPendingAnnouncements(appVersion || undefined);
            if (announcements.length > 0) {
              pendingAnnouncements = announcements;
              showAnnouncementModal = true;
              announcementsShown = true;
            }
          } catch (err) {
            console.error("Failed to fetch announcements:", err);
          }

          let updateShown = false;
          try {
            const updateInfo = await checkForUpdates({
              currentVersion: appVersion,
            });
            if (updateInfo) {
              pendingUpdate = updateInfo;
              if (pendingAnnouncements.length === 0) {
                showUpdateModal = true;
                updateShown = true;
              }
            }
          } catch (err) {
            console.error("Failed to check for updates:", err);
          }

          if (!announcementsShown && !updateShown) {
            await checkWorkshopDownload();
          }
        });
      }
    };

    if (window.pywebview?.api) {
      await run();
      return;
    }
    window.addEventListener("pywebviewready", run, { once: true });
    setTimeout(dismissLoader, 3000);
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

    window.onLogReceived = (logEntry: { text: string; type: string; timestamp?: string }) => {
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

  async function triggerPatch() {
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

  async function handlePatch() {
    if (isPatching) return;

    try {
      const needsWorkshop = await window.pywebview?.api?.check_workshop_tools_needed?.();
      if (needsWorkshop) {
        showWorkshopModal = true;
        return;
      }
    } catch (err) {
      console.error("Error checking workshop tools:", err);
    }

    await triggerPatch();
  }

  async function handleWorkshopExtract() {
    showWorkshopModal = false;
    isPatching = true;
    activeTab = "terminal";
    try {
      await window.pywebview?.api?.extract_workshop_tools?.();
    } catch (err) {
      logs = [
        ...logs,
        {
          text: `Error extracting workshop tools: ${err}`,
          type: "error",
          timestamp: getCurrentTime(),
        },
      ];
    }
    await triggerPatch();
  }

  async function handleWorkshopSkip() {
    showWorkshopModal = false;
    await triggerPatch();
  }

  function handleWorkshopCancel() {
    showWorkshopModal = false;
  }

  async function handleUninstallConfirm(removeEverything: boolean) {
    showUninstallModal = false;
    if (isPatching) return;

    isPatching = true;
    activeTab = "terminal";
    try {
      await window.pywebview?.api?.start_uninstall(removeEverything);
    } catch (err) {
      logs = [
        ...logs,
        {
          text: `Error triggering uninstall: ${err}`,
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
        broadcastToPlugins({ type: "LOCALE_CHANGED", lang, dict });
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
    } catch (err) {
      console.error("Error setting game language:", err);
    }
  }
  function broadcastToPlugins(message: any) {
    const iframes = document.querySelectorAll<HTMLIFrameElement>("iframe.plugin-frame");
    iframes.forEach((frame) => {
      try {
        frame.contentWindow?.postMessage(message, "*");
      } catch (e) {
        // ignore
      }
    });
  }

  async function handleSaveMods(data: Record<string, boolean>) {
    try {
      await window.pywebview?.api?.set_mods(data);
      broadcastToPlugins({ type: "MODS_UPDATED" });
    } catch (err) {
      console.error("Failed to save mod state:", err);
    }
  }

  async function handleSettingChange(key: string, value: any) {
    if (key === "theme") {
      await applyTheme(value);
    } else if (key === "locale") {
      await handleLanguageChange(value);
    } else if (key === "output_locale") {
      await handleGameLanguageChange(value);
    }
  }

  async function handleDismissAnnouncement(id: string) {
    await markAnnouncementSeen(id);
    pendingAnnouncements = pendingAnnouncements.filter((a) => {
      const annId = a.time ? a.time.replace(/[-+]/g, "").split("=")[0].trim() : "";
      return annId !== id;
    });
    if (pendingAnnouncements.length === 0) {
      showAnnouncementModal = false;
      if (pendingUpdate) {
        showUpdateModal = true;
      } else {
        await checkWorkshopDownload();
      }
    }
  }

  async function handleCloseAnnouncements() {
    showAnnouncementModal = false;
    if (pendingUpdate) {
      showUpdateModal = true;
    } else {
      await checkWorkshopDownload();
    }
  }

  function handlePerformUpdate(url: string) {
    showUpdateModal = false;
    if (url) {
      window.open(url, "_blank");
    }
  }

  async function handleIgnoreUpdate(version: string) {
    await ignoreUpdate(version);
    showUpdateModal = false;
    await checkWorkshopDownload();
  }

  async function handleCloseUpdateModal() {
    showUpdateModal = false;
    await checkWorkshopDownload();
  }

  async function checkWorkshopDownload() {
    try {
      const isInstalled = await window.pywebview?.api?.is_workshop_installed?.();
      if (isInstalled === false) {
        const ignored = await window.pywebview?.api?.get_state?.("ignore_workshop_download");
        if (!ignored) {
          showWorkshopDownloadModal = true;
        }
      }
    } catch (err) {
      console.error("Failed to check workshop status:", err);
    }
  }

  async function handleIgnoreWorkshopDownload() {
    showWorkshopDownloadModal = false;
    try {
      await window.pywebview?.api?.set_state?.("ignore_workshop_download", true);
    } catch (err) {
      console.error("Failed to save ignore_workshop_download state:", err);
    }
  }

  function handleLaterWorkshopDownload() {
    showWorkshopDownloadModal = false;
  }

  async function handleWorkshopDownloadSuccess() {
    showWorkshopDownloadModal = false;
    await refreshMods();
  }
</script>

<div class="app-container">
  <Header
    {activeTab}
    {isPatching}
    {pluginTabs}
    onTabChange={(tab) => {
      activeTab = tab;
      broadcastToPlugins({ type: "TAB_ACTIVE", tab });
    }}
    onPatch={handlePatch}
    onUninstallClick={() => (showUninstallModal = true)}
  />

  <UninstallModal
    isOpen={showUninstallModal}
    onConfirm={handleUninstallConfirm}
    onCancel={() => (showUninstallModal = false)}
  />

  <AnnouncementModal
    isOpen={showAnnouncementModal}
    announcements={pendingAnnouncements}
    onDismiss={handleDismissAnnouncement}
    onClose={handleCloseAnnouncements}
  />

  <UpdateModal
    isOpen={showUpdateModal}
    updateInfo={pendingUpdate}
    {downloads}
    onIgnore={handleIgnoreUpdate}
    onClose={handleCloseUpdateModal}
  />

  <WorkshopToolsDetectedModal
    isOpen={showWorkshopModal}
    onExtract={handleWorkshopExtract}
    onSkip={handleWorkshopSkip}
    onCancel={handleWorkshopCancel}
  />

  <WorkshopDownloadModal
    isOpen={showWorkshopDownloadModal}
    onIgnore={handleIgnoreWorkshopDownload}
    onLater={handleLaterWorkshopDownload}
    onSuccess={handleWorkshopDownloadSuccess}
  />

  <main class="content-area">
    <div class="tab-pane" class:hidden={activeTab !== "mods"}>
      <ModGrid onSaveMods={handleSaveMods} />
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
      <Settings active={activeTab === "settings"} onSettingChange={handleSettingChange} />
    </div>

    {#each pluginTabs as plugin}
      <div class="tab-pane" class:hidden={activeTab !== plugin.id}>
        {#if pluginContents[plugin.id]}
          <iframe
            srcdoc={pluginContents[plugin.id]}
            title={plugin.name}
            class="plugin-frame"
            allowtransparency={true}
            on:load={(e) => injectThemeIntoFrame(e.currentTarget)}
          ></iframe>
        {:else if plugin.entry_point && !plugin.entry_point.startsWith("file://")}
          <iframe
            src={plugin.entry_point}
            title={plugin.name}
            class="plugin-frame"
            allowtransparency={true}
            on:load={(e) => injectThemeIntoFrame(e.currentTarget)}
          ></iframe>
        {/if}
      </div>
    {/each}
  </main>

  <div class="download-stack">
    <DownloadNotification {downloads} onDismiss={handleDismissDownload} />
  </div>
</div>

<style>
  :global(*),
  :global(*::before),
  :global(*::after) {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    border-radius: 0;
    box-shadow: none;
    transition: none;
    animation: none;
  }

  :global(body),
  :global(html) {
    width: 100%;
    height: 100%;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: var(--text-primary, #000);
    background: var(--bg-primary, #fff);
    overflow: hidden;
  }

  .app-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #000);
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
    background: transparent;
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
