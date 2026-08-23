<script lang="ts">
  import { modsStore } from "../stores/mods";
  import { localeStore } from "../stores/locale";
  import { resolveText } from "../i18n";
  import ModCard from "./ModCard.svelte";

  export let onSaveMods: (data: Record<string, boolean>) => void;

  let searchQuery = "";

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
        <button on:click={() => (searchQuery = "")}> Clear Search </button>
      {/if}
    </div>
  </div>

  <div class="mod-grid">
    {#each filteredMods as mod (mod.name)}
      <ModCard
        name={mod.name}
        enabled={mod.enabled}
        ontoggle={(value) => toggleMod(mod.name, value)}
      />
    {/each}
  </div>
</div>

<style>
  .mod-grid-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    gap: 8px;
    min-height: 0;
    overflow: hidden;
  }

  .grid-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px;
    border-bottom: 1px solid #ccc;
    gap: 8px;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .search-box input {
    padding: 4px 8px;
    font-size: 13px;
  }

  .mod-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    grid-auto-rows: minmax(40px, auto);
    align-content: start;
    gap: 8px;
    padding: 8px;
    overflow-y: auto;
    flex: 1;
    min-height: 0;
  }
</style>
