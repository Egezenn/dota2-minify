<script lang="ts">
  import { modsStore } from "../stores/mods";
  import { localeStore } from "../stores/locale";
  import { resolveText } from "../i18n";
  import ModCard from "./ModCard.svelte";
  import ModDetailsModal from "./ModDetailsModal.svelte";

  export let onSaveMods: (data: Record<string, boolean>) => void;

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
    onSaveMods(payload);
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

  <div class="mod-grid">
    {#each filteredMods as mod (mod.name)}
      <ModCard
        name={mod.name}
        enabled={mod.enabled}
        always={mod.always}
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
    gap: 8px;
    overflow: hidden;
  }

  .grid-toolbar {
    display: flex;
    align-items: center;
    padding: 8px;
    border-bottom: 1px solid #000;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .search-box input {
    padding: 4px 8px;
    border: 1px solid #000;
    font-size: 13px;
  }

  .search-box button {
    padding: 4px 8px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    cursor: pointer;
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
