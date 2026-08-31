<script lang="ts">
  import { modsStore } from "../stores/mods";
  import { localeStore } from "../stores/locale";
  import { resolveText } from "../i18n";
  import ModCard from "./ModCard.svelte";
  import ModDetailsModal from "./ModDetailsModal.svelte";

  export let onSaveMods: ((data: Record<string, boolean>) => void) | undefined =
    undefined;

  let searchQuery = "";
  let selectedModForDetails: string | null = null;

  $: dict = $localeStore.dict;
  $: mods = $modsStore;

  $: filteredMods = mods.filter((mod) =>
    mod.name.toLowerCase().includes(searchQuery.toLowerCase().trim()),
  );

  function toggleMod(modName: string, enabled: boolean) {
    const updated = mods.map((m) =>
      m.name === modName ? { ...m, enabled } : m,
    );
    modsStore.set(updated);

    const payload: Record<string, boolean> = {};
    updated.forEach((m) => (payload[m.name] = m.enabled));
    if (onSaveMods) onSaveMods(payload);
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
      <h3>Mods</h3>
    </div>
    <div class="toolbar-controls">
      <div class="search-box">
        <input
          type="text"
          placeholder="Search mods..."
          bind:value={searchQuery}
        />
        {#if searchQuery}
          <button on:click={() => (searchQuery = "")}> Clear </button>
        {/if}
      </div>
    </div>
  </div>

  <div class="mod-grid">
    {#each filteredMods as mod (mod.name)}
      <ModCard
        name={mod.name}
        enabled={mod.enabled}
        always={mod.always}
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
    border-bottom: 1px solid #000;
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

  .search-box {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .search-box input {
    height: 24px;
    padding: 0 8px;
    border: 1px solid #000;
    font-size: 13px;
    box-sizing: border-box;
  }

  .search-box button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 8px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    cursor: pointer;
    line-height: 1;
    box-sizing: border-box;
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
