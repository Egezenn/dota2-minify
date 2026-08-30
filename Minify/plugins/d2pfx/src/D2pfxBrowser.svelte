<script lang="ts">
  import { onMount } from "svelte";

  interface Category {
    id: string;
    name: string;
    description: string;
  }

  interface D2Mod {
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

  interface InstalledMod {
    name: string;
    category: string;
    label?: string;
    folder: string;
  }

  let categories: Category[] = [];
  let selectedCategory: string = "";
  let selectedCatName: string = "";
  let selectedCatDesc: string = "";

  let mods: D2Mod[] = [];
  let installedMods: InstalledMod[] = [];

  let catSearchQuery = "";
  let modSearchQuery = "";

  let isLoadingCategories = false;
  let isLoadingMods = false;
  let installingMap: Record<string, boolean> = {};
  let actionMessage = "";

  $: filteredCategories = categories.filter((c) =>
    c.name.toLowerCase().includes(catSearchQuery.toLowerCase())
  );

  function getApi() {
    if (window.pywebview && window.pywebview.api) {
      return window.pywebview.api;
    }
    if (window.parent && (window.parent as any).pywebview && (window.parent as any).pywebview.api) {
      return (window.parent as any).pywebview.api;
    }
    return null;
  }

  async function callApi(action: string, params: Record<string, any> = {}): Promise<any> {
    const api = getApi();
    if (!api || !api.call_plugin_api) {
      throw new Error("API not connected");
    }
    return api.call_plugin_api("d2pfx", action, params);
  }

  function getModKey(m: D2Mod, catId: string): string {
    return `${catId}::${m.name}::${m.label || ""}`;
  }

  function isInstalled(m: D2Mod, catId: string): boolean {
    return installedMods.some(
      (inst) =>
        inst.name === m.name &&
        inst.category === catId &&
        (inst.label || "") === (m.label || "")
    );
  }

  async function loadCategories() {
    isLoadingCategories = true;
    try {
      const res = await callApi("get_categories");
      categories = Array.isArray(res) ? res : [];
      if (categories.length > 0 && !selectedCategory) {
        selectCategory(categories[0]);
      }
    } catch (err) {
      console.error("Error loading D2PFX categories:", err);
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

  async function handleInstall(m: D2Mod) {
    const key = getModKey(m, selectedCategory);
    installingMap = { ...installingMap, [key]: true };
    actionMessage = `Installing ${m.name}...`;
    try {
      const res = await callApi("install_mod", { mod: m, cat_id: selectedCategory });
      if (res?.success) {
        await refreshInstalledMods();
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

  async function handlePruneImages() {
    actionMessage = "Clearing image cache...";
    try {
      await callApi("prune_image_cache");
      if (selectedCategory) await fetchMods();
      actionMessage = "Image cache cleared.";
    } catch (err) {
      actionMessage = `Prune error: ${err}`;
    } finally {
      setTimeout(() => (actionMessage = ""), 3000);
    }
  }

  function formatAuthors(author: any, sender: any): string {
    const parts: string[] = [];
    if (author) {
      if (Array.isArray(author)) parts.push(`By: ${author.join(", ")}`);
      else parts.push(`By: ${author}`);
    }
    if (sender) {
      if (Array.isArray(sender)) parts.push(`Sender: ${sender.join(", ")}`);
      else parts.push(`Sender: ${sender}`);
    }
    return parts.join(" | ");
  }

  function formatTags(tags: any): string {
    if (!tags) return "";
    if (Array.isArray(tags)) return tags.join(", ");
    if (typeof tags === "object") return Object.keys(tags).filter((k) => tags[k]).join(", ");
    return String(tags);
  }

  function handleImageError(event: Event) {
    const target = event.currentTarget as HTMLElement;
    if (target) {
      target.style.display = "none";
    }
  }

  onMount(() => {
    const init = () => {
      if (getApi()) {
        loadCategories();
        refreshInstalledMods();
      } else {
        setTimeout(init, 100);
      }
    };
    init();
  });
</script>

<div class="d2pfx-container">
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-search">
      <input
        type="text"
        placeholder="Search categories..."
        bind:value={catSearchQuery}
      />
    </div>
    <div class="category-list">
      {#if isLoadingCategories}
        <div class="loading-item">Loading categories...</div>
      {:else}
        {#each filteredCategories as cat}
          <button
            class="category-item {selectedCategory === cat.id ? 'active' : ''}"
            on:click={() => selectCategory(cat)}
          >
            {cat.name}
          </button>
        {/each}
      {/if}
    </div>
  </aside>

  <!-- Main View -->
  <main class="main-pane">
    <header class="top-bar">
      <div class="cat-info">
        <h2>{selectedCatName || "Select a category"}</h2>
        {#if selectedCatDesc}
          <p>{selectedCatDesc}</p>
        {/if}
      </div>

      <div class="top-actions">
        <input
          type="text"
          placeholder="Search mods..."
          bind:value={modSearchQuery}
          on:input={() => fetchMods()}
        />

        <button class="action-btn" on:click={handlePruneMetadata}>
          Refresh Data
        </button>

        <button class="action-btn" on:click={handlePruneImages}>
          Clear Imgs
        </button>
      </div>
    </header>

    {#if actionMessage}
      <div class="status-banner">{actionMessage}</div>
    {/if}

    <div class="mods-grid-container">
      {#if isLoadingMods}
        <div class="loading-grid">Loading mods...</div>
      {:else if mods.length === 0}
        <div class="empty-grid">No mods found in this category.</div>
      {:else}
        <div class="mods-grid">
          {#each mods as m}
            {@const key = getModKey(m, selectedCategory)}
            {@const installed = isInstalled(m, selectedCategory)}
            {@const inProgress = Boolean(installingMap[key])}
            <div class="mod-card">
              <div class="preview-box">
                {#if m.preview_url}
                  <img
                    src={m.preview_url}
                    alt={m.name}
                    class="preview-img"
                    on:error={handleImageError}
                  />
                {:else}
                  <span class="no-preview">NO PREVIEW</span>
                {/if}
              </div>

              <div class="card-details">
                <div class="mod-title">
                  {m.name}{m.label ? ` (${m.label})` : ""}
                </div>

                {#if formatAuthors(m.author, m.sender)}
                  <div class="mod-meta">
                    {formatAuthors(m.author, m.sender)}
                  </div>
                {/if}

                {#if formatTags(m.tags)}
                  <div class="mod-tags">
                    {formatTags(m.tags)}
                  </div>
                {/if}
              </div>

              <div class="card-actions">
                {#if installed}
                  <button
                    class="install-btn installed"
                    disabled={inProgress}
                    on:click={() => handleUninstall(m)}
                  >
                    {inProgress ? "REMOVING..." : "REMOVE"}
                  </button>
                {:else}
                  <button
                    class="install-btn"
                    disabled={inProgress}
                    on:click={() => handleInstall(m)}
                  >
                    {inProgress ? "INSTALLING..." : "INSTALL"}
                  </button>
                {/if}
              </div>
            </div>
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
    background: #fff;
    color: #000;
    font-family: inherit;
    font-size: 13px;
  }

  .sidebar {
    width: 180px;
    border-right: 1px solid #000;
    display: flex;
    flex-direction: column;
    background: #fff;
    flex-shrink: 0;
  }

  .sidebar-search {
    padding: 6px;
    border-bottom: 1px solid #000;
  }

  .sidebar-search input {
    width: 100%;
    padding: 4px 6px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-size: 12px;
    outline: none;
  }

  .category-list {
    flex: 1;
    overflow-y: auto;
  }

  .loading-item {
    padding: 8px;
    font-size: 11px;
    color: #666;
  }

  .category-item {
    width: 100%;
    padding: 6px 8px;
    text-align: left;
    border: none;
    border-bottom: 1px solid #eee;
    background: #fff;
    color: #000;
    cursor: pointer;
    font-size: 12px;
  }

  .category-item:hover,
  .category-item.active {
    background: #000;
    color: #fff;
  }

  .main-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid #000;
    background: #fff;
    gap: 12px;
  }

  .cat-info h2 {
    font-size: 14px;
    font-weight: bold;
    text-transform: capitalize;
  }

  .cat-info p {
    font-size: 11px;
    color: #555;
    margin-top: 2px;
  }

  .top-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .top-actions input {
    padding: 4px 6px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    outline: none;
    font-size: 12px;
    width: 140px;
  }

  .action-btn {
    padding: 4px 8px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    cursor: pointer;
    font-weight: bold;
    font-size: 11px;
  }

  .action-btn:hover {
    background: #000;
    color: #fff;
  }

  .status-banner {
    padding: 4px 12px;
    background: #000;
    color: #fff;
    font-size: 11px;
    font-weight: bold;
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

  .mod-card {
    border: 1px solid #000;
    padding: 8px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: #fff;
  }

  .preview-box {
    width: 100%;
    height: 100px;
    border: 1px solid #000;
    background: #f8f8f8;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    margin-bottom: 6px;
  }

  .preview-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .no-preview {
    font-size: 10px;
    color: #888;
  }

  .card-details {
    flex: 1;
    margin-bottom: 6px;
  }

  .mod-title {
    font-weight: bold;
    font-size: 12px;
    margin-bottom: 2px;
    line-height: 1.2;
  }

  .mod-meta {
    font-size: 10px;
    color: #555;
    margin-bottom: 2px;
  }

  .mod-tags {
    font-size: 9px;
    color: #0055bb;
    word-break: break-all;
  }

  .card-actions {
    margin-top: 4px;
  }

  .install-btn {
    width: 100%;
    padding: 4px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-weight: bold;
    cursor: pointer;
    font-size: 11px;
  }

  .install-btn.installed {
    background: #000;
    color: #fff;
  }

  .install-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
