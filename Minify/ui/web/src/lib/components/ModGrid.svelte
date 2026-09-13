<script lang="ts">
  import { modsStore } from "../stores/mods";
  import { localeStore } from "../stores/locale";
  import { t } from "../i18n";
  import { refreshMods } from "../api";
  import ModCard from "./ModCard.svelte";
  import ModDetailsModal from "./ModDetailsModal.svelte";

  export let onSaveMods: ((data: Record<string, boolean>) => void) | undefined = undefined;

  let searchQuery = "";
  let selectedModForDetails: string | null = null;
  let isRefreshing = false;

  async function handleRefresh() {
    if (isRefreshing) return;
    isRefreshing = true;
    try {
      await refreshMods();
    } finally {
      setTimeout(() => {
        isRefreshing = false;
      }, 300);
    }
  }

  $: mods = $modsStore;

  $: filteredMods = mods.filter((mod) => {
    const q = searchQuery.toLowerCase().trim();
    return (mod.display_name && mod.display_name.toLowerCase().includes(q)) || mod.name.toLowerCase().includes(q);
  });

  async function toggleMod(modName: string, enabled: boolean) {
    const updated = mods.map((m) => (m.name === modName ? { ...m, enabled } : m));
    modsStore.set(updated);

    const payload: Record<string, boolean> = {};
    updated.forEach((m) => (payload[m.name] = m.enabled));
    if (onSaveMods) {
      onSaveMods(payload);
    } else if (window.pywebview?.api?.set_mods) {
      try {
        await window.pywebview.api.set_mods(payload);
      } catch (err) {
        console.error("Failed to save mods:", err);
      }
    }
  }

  function openDetails(modName: string) {
    selectedModForDetails = modName;
  }

  function closeDetails() {
    selectedModForDetails = null;
  }
</script>

<div class="mod-grid-container">
  <div class="grid-toolbar">
    <div class="toolbar-title">
      <h3>{$t("title_mods")}</h3>
    </div>
    <div class="toolbar-controls">
      <button class="refresh-btn" class:refreshing={isRefreshing} on:click={handleRefresh} title={$t("button_refresh")}>
        <span class="refresh-icon" class:spin={isRefreshing}>↻</span>
        {$t("button_refresh")}
      </button>
      <div class="search-box">
        <input type="text" placeholder={$t("placeholder_search_mods")} bind:value={searchQuery} />
        {#if searchQuery}
          <button on:click={() => (searchQuery = "")}>
            {$t("button_clear")}
          </button>
        {/if}
      </div>
    </div>
  </div>

  <div class="mod-grid">
    {#each filteredMods as mod (mod.name)}
      <ModCard
        name={mod.name}
        displayName={mod.display_name}
        enabled={mod.enabled}
        always={mod.always}
        untickable={mod.untickable}
        preview={mod.preview}
        ontoggle={(value) => toggleMod(mod.name, value)}
        onDetails={openDetails}
      />
    {/each}
  </div>

  <ModDetailsModal modName={selectedModForDetails} onClose={closeDetails} />
</div>

<style>
  .mod-grid-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  .grid-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 38px;
    padding: 0 8px;
    border-bottom: 1px solid var(--border-color, #000);
    font-size: 13px;
    box-sizing: border-box;
  }

  .toolbar-title {
    display: flex;
    align-items: center;
  }

  .toolbar-title h3 {
    margin: 0;
    font-size: 15px;
    font-weight: bold;
    line-height: 1;
    display: flex;
    align-items: center;
  }

  .toolbar-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .refresh-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 4px;
    height: 24px;
    padding: 0 8px;
    border: 1px solid var(--btn-border, #000);
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    font-size: 12px;
    cursor: pointer;
    line-height: 1;
    box-sizing: border-box;
  }

  .refresh-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .refresh-btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .refresh-icon {
    display: inline-block;
    font-size: 14px;
    line-height: 1;
  }

  .refresh-icon.spin {
    animation: spin 0.6s linear infinite;
  }

  @keyframes spin {
    100% {
      transform: rotate(360deg);
    }
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .search-box input {
    height: 24px;
    padding: 0 8px;
    border: 1px solid var(--input-border, #000);
    background: var(--input-bg, #fff);
    color: var(--input-text, #000);
    font-size: 13px;
    box-sizing: border-box;
  }

  .search-box button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 8px;
    border: 1px solid var(--btn-border, #000);
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    cursor: pointer;
    line-height: 1;
    box-sizing: border-box;
  }

  .search-box button:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .mod-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    align-content: start;
    gap: 8px;
    padding: 8px;
    overflow-y: auto;
    flex: 1;
  }
</style>
