<script lang="ts">
  import { onMount } from "svelte";
  import type { Category, D2Mod, InstalledMod } from "./lib/types";
  import { callApi, getApi, getModKey, isInstalled, notifyParentModsRefreshed } from "./lib/api";
  import Sidebar from "./lib/components/Sidebar.svelte";
  import Header from "./lib/components/Header.svelte";
  import ModCard from "./lib/components/ModCard.svelte";

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
  let actionMessage = "";

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
    } catch (err) {
      console.error("Error loading installed D2PFX mods:", err);
      installedMods = [];
    }
  }

  async function selectCategory(cat: Category) {
    selectedCategory = cat.id;
    selectedCatName = cat.name;
    selectedCatDesc = cat.description;
    await fetchMods();
  }

  async function fetchMods() {
    if (!selectedCategory) return;
    isLoadingMods = true;
    try {
      const res = await callApi("get_mods", { cat_id: selectedCategory, search: modSearchQuery });
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
    actionMessage = `Installing ${m.name}...`;
    try {
      const res = await callApi("install_mod", { mod: m, cat_id: selectedCategory });
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
    const init = async () => {
      if (getApi()) {
        await loadCategories();
        await refreshInstalledMods();
      } else {
        setTimeout(init, 100);
      }
    };
    init();
  });
</script>

<div class="d2pfx-container">
  <Sidebar
    {categories}
    {selectedCategory}
    {isLoadingCategories}
    onSelectCategory={selectCategory}
  />

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
        <div class="loading-grid">Loading mods...</div>
      {:else if mods.length === 0}
        <div class="empty-grid">No mods found in this category.</div>
      {:else}
        <div class="mods-grid">
          {#each mods as m}
            {@const key = getModKey(m, selectedCategory)}
            <ModCard
              mod={m}
              installed={isInstalled(m, selectedCategory, installedMods)}
              inProgress={Boolean(installingMap[key])}
              onInstall={handleInstall}
              onUninstall={handleUninstall}
            />
          {/each}
        </div>
      {/if}
    </div>
  </main>
</div>

<style>
  *,
  *::before,
  *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    border-radius: 0 !important;
    box-shadow: none !important;
    transition: none !important;
    animation: none !important;
  }

  :global(body), :global(html) {
    width: 100%;
    height: 100%;
    margin: 0 !important;
    padding: 0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #000;
    background: #fff;
    overflow: hidden;
  }

  .d2pfx-container {
    display: flex;
    height: 100vh;
    width: 100vw;
    margin: 0 !important;
    padding: 0 !important;
    background: #fff;
    color: #000;
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
    color: #666;
  }

  .mods-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
    gap: 10px;
  }
</style>
