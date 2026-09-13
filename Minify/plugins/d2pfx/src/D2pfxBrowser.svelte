<script lang="ts">
  import { onMount } from "svelte";
  import type { Category, D2Mod, InstalledMod } from "./lib/types";
  import { callApi, getApi, getModKey, isInstalled, notifyParentModsRefreshed, setModState } from "./lib/api";
  import Sidebar from "./lib/components/Sidebar.svelte";
  import Header from "./lib/components/Header.svelte";
  import ModCard from "./lib/components/ModCard.svelte";
  import { t, setPluginLocale } from "./lib/i18n";

  let categories: Category[] = [];
  let selectedCategory: string = "";
  let selectedCatName: string = "";
  let selectedCatDesc: string = "";

  let mods: D2Mod[] = [];
  let installedMods: InstalledMod[] = [];
  let modSearchQuery = "";

  let isLoadingCategories = false;
  let isLoadingMods = false;
  let installingMap: Record<string, boolean> = {};
  let enabledMap: Record<string, boolean> = {};
  let actionMessage = "";
  let previewModal: { url: string; title: string } | null = null;

  function openPreview(url: string, title: string) {
    previewModal = { url, title };
  }

  function closePreview() {
    previewModal = null;
  }

  async function loadCategories() {
    isLoadingCategories = true;
    try {
      const res = await callApi("get_categories");
      categories = Array.isArray(res) ? res : [];
      if (categories.length > 0 && !selectedCategory) {
        await selectCategory(categories[0]);
      }
    } catch (err) {
      console.error("Error loading D2PFX categories:", err);
      actionMessage = `Error loading categories: ${err}`;
      categories = [];
    } finally {
      isLoadingCategories = false;
    }
  }

  async function refreshInstalledMods() {
    try {
      const res = await callApi("get_installed_mods");
      installedMods = Array.isArray(res) ? res : [];
      const updated: Record<string, boolean> = { ...enabledMap };
      for (const inst of installedMods) {
        const key = `${inst.category}::${inst.name}::${inst.label || ""}`;
        if (inst.enabled !== undefined) {
          updated[key] = Boolean(inst.enabled);
        }
      }
      enabledMap = updated;
    } catch (err) {
      console.error("Error loading installed D2PFX mods:", err);
      installedMods = [];
    }
  }

  async function selectCategory(cat: Category) {
    selectedCategory = cat.id;
    selectedCatName = cat.name;
    selectedCatDesc = cat.description;
    await Promise.all([fetchMods(), refreshInstalledMods()]);
  }

  async function fetchMods() {
    if (!selectedCategory) return;
    isLoadingMods = true;
    try {
      const res = await callApi("get_mods", {
        cat_id: selectedCategory,
        search: modSearchQuery,
      });
      mods = Array.isArray(res) ? res : [];
    } catch (err) {
      console.error("Error fetching D2PFX mods:", err);
      mods = [];
    } finally {
      isLoadingMods = false;
    }
  }

  function handleSearchChange(query: string) {
    modSearchQuery = query;
    fetchMods();
  }

  async function handleInstall(m: D2Mod) {
    const key = getModKey(m, selectedCategory);
    installingMap = { ...installingMap, [key]: true };
    enabledMap = { ...enabledMap, [key]: true };
    actionMessage = `Installing ${m.name}...`;

    try {
      await setModState(m.name, selectedCategory, m.label, true);
      notifyParentModsRefreshed();
    } catch (err) {
      console.error("Error setting mod initial state in mods.json:", err);
    }

    try {
      const res = await callApi("install_mod", {
        mod: m,
        cat_id: selectedCategory,
      });
      if (res?.success) {
        await refreshInstalledMods();
        notifyParentModsRefreshed();
        actionMessage = `Successfully installed ${m.name}`;
      } else {
        actionMessage = `Failed: ${res?.error || "Unknown error"}`;
      }
    } catch (err) {
      actionMessage = `Install error: ${err}`;
    } finally {
      const copy = { ...installingMap };
      delete copy[key];
      installingMap = copy;
      setTimeout(() => (actionMessage = ""), 4000);
    }
  }

  async function handleToggleEnabled(m: D2Mod, nextEnabled: boolean) {
    const key = getModKey(m, selectedCategory);
    enabledMap = { ...enabledMap, [key]: nextEnabled };
    try {
      await setModState(m.name, selectedCategory, m.label, nextEnabled);
      notifyParentModsRefreshed();
    } catch (err) {
      console.error("Error toggling mod state in mods.json:", err);
    }
  }

  async function handleUninstall(m: D2Mod) {
    const key = getModKey(m, selectedCategory);
    installingMap = { ...installingMap, [key]: true };
    actionMessage = `Removing ${m.name}...`;
    try {
      const res = await callApi("uninstall_mod", {
        mod_name: m.name,
        cat_id: selectedCategory,
        label: m.label,
      });
      if (res?.success) {
        const copyEnabled = { ...enabledMap };
        delete copyEnabled[key];
        enabledMap = copyEnabled;
        await refreshInstalledMods();
        notifyParentModsRefreshed();
        actionMessage = `Successfully removed ${m.name}`;
      } else {
        actionMessage = `Failed: ${res?.error || "Unknown error"}`;
      }
    } catch (err) {
      actionMessage = `Remove error: ${err}`;
    } finally {
      const copy = { ...installingMap };
      delete copy[key];
      installingMap = copy;
      setTimeout(() => (actionMessage = ""), 4000);
    }
  }

  async function handlePruneMetadata() {
    actionMessage = "Refreshing metadata cache...";
    try {
      await callApi("prune_metadata_cache");
      await loadCategories();
      if (selectedCategory) await fetchMods();
      actionMessage = "Metadata cache refreshed.";
    } catch (err) {
      actionMessage = `Prune error: ${err}`;
    } finally {
      setTimeout(() => (actionMessage = ""), 3000);
    }
  }

  onMount(() => {
    const handleParentMessage = (e: MessageEvent) => {
      if (e.data?.type === "MODS_UPDATED" || e.data?.type === "TAB_ACTIVE" || e.data?.type === "REFRESH_MODS") {
        refreshInstalledMods();
      } else if (e.data?.type === "LOCALE_CHANGED" && e.data.lang) {
        setPluginLocale(e.data.lang, e.data.dict);
      }
    };

    try {
      const parentApi = (window.parent as any)?.pywebview?.api;
      if (parentApi?.get_current_locale) {
        Promise.all([parentApi.get_current_locale(), parentApi.get_localization ? parentApi.get_localization() : null])
          .then(([lang, dict]) => {
            if (lang) setPluginLocale(lang, dict || {});
          })
          .catch(() => {});
      }
    } catch (_) {}

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && previewModal) {
        e.preventDefault();
        e.stopPropagation();
        closePreview();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("message", handleParentMessage);
    window.addEventListener("focus", refreshInstalledMods);

    const handleVisibility = () => {
      if (!document.hidden) {
        refreshInstalledMods();
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);

    const init = async () => {
      if (getApi()) {
        await loadCategories();
        await refreshInstalledMods();
      } else {
        setTimeout(init, 100);
      }
    };
    init();

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("message", handleParentMessage);
      window.removeEventListener("focus", refreshInstalledMods);
      document.removeEventListener("visibilitychange", handleVisibility);
    };
  });
</script>

<div class="d2pfx-container">
  <Sidebar {categories} {selectedCategory} {isLoadingCategories} onSelectCategory={selectCategory} />

  <main class="main-pane">
    <Header
      categoryName={selectedCatName}
      categoryDesc={selectedCatDesc}
      searchQuery={modSearchQuery}
      onSearchChange={handleSearchChange}
      onRefreshData={handlePruneMetadata}
    />

    <div class="mods-grid-container">
      {#if isLoadingMods}
        <div class="loading-grid">{$t("label_loading_mods")}</div>
      {:else if mods.length === 0}
        <div class="empty-grid">{$t("label_no_mods_found")}</div>
      {:else}
        <div class="mods-grid">
          {#each mods as m}
            {@const key = getModKey(m, selectedCategory)}
            <ModCard
              mod={m}
              installed={isInstalled(m, selectedCategory, installedMods)}
              inProgress={Boolean(installingMap[key])}
              enabled={Boolean(enabledMap[key])}
              onInstall={handleInstall}
              onUninstall={handleUninstall}
              onToggleEnabled={handleToggleEnabled}
              onPreview={openPreview}
            />
          {/each}
        </div>
      {/if}
    </div>
  </main>

  {#if previewModal}
    <div
      class="lightbox-backdrop"
      on:click|stopPropagation={closePreview}
      role="button"
      tabindex="-1"
      on:keydown={(e) => {
        if (e.key === "Escape") {
          e.stopPropagation();
          e.preventDefault();
          closePreview();
        }
      }}
    >
      <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <div class="lightbox-card" on:click|stopPropagation role="dialog" aria-modal="true" aria-label="Image Preview">
        <header class="lightbox-header">
          <span class="lightbox-title">{previewModal.title} - {$t("label_preview")}</span>
          <button
            class="close-btn"
            type="button"
            on:click|stopPropagation={closePreview}
            aria-label={$t("button_close")}
          >
            &times;
          </button>
        </header>
        <div
          class="lightbox-body"
          role="button"
          tabindex="-1"
          on:click|stopPropagation={closePreview}
          on:keydown={(e) => {
            if (e.key === "Enter" || e.key === " " || e.key === "Escape") {
              e.stopPropagation();
              e.preventDefault();
              closePreview();
            }
          }}
          title={$t("title_click_to_close")}
        >
          <img src={previewModal.url} alt={previewModal.title} />
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .d2pfx-container {
    display: flex;
    height: 100vh;
    width: 100vw;
    margin: 0;
    padding: 0;
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #000);
    font-family: inherit;
    font-size: 13px;
  }

  .main-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .mods-grid-container {
    flex: 1;
    padding: 10px;
    overflow-y: auto;
  }

  .loading-grid,
  .empty-grid {
    padding: 16px;
    font-size: 12px;
    color: var(--text-secondary, #666);
  }

  .mods-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
    gap: 10px;
  }

  .lightbox-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .lightbox-card {
    background: var(--modal-bg, #fff);
    border: 1px solid var(--modal-border, #000);
    display: flex;
    flex-direction: column;
    max-width: 92vw;
    max-height: 92vh;
    box-sizing: border-box;
  }

  .lightbox-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 38px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--border-color, #000);
    background: var(--modal-bg, #fff);
    gap: 12px;
    box-sizing: border-box;
  }

  .lightbox-title {
    font-size: 13px;
    font-weight: bold;
    color: var(--text-primary, #000);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .close-btn {
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    border: 1px solid var(--btn-border, #000);
    padding: 2px 8px;
    cursor: pointer;
  }

  .close-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .close-btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .lightbox-body {
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: 12px;
    background: var(--terminal-bg, var(--bg-primary, #000));
    cursor: zoom-out;
  }

  .lightbox-body img {
    max-width: 88vw;
    max-height: 80vh;
    object-fit: contain;
    display: block;
  }
</style>
