<script lang="ts">
  export let activeTab: "mods" | "terminal" | "settings";
  export let currentGameLang: string;
  export let availableGameLangs: string[];
  export let isPatching: boolean;
  export let onTabChange: (tab: "mods" | "terminal" | "settings") => void;
  export let onGameLangChange: (event: Event) => void;
  export let onPatch: () => void;
</script>

<header class="header">
  <nav class="nav-tabs">
    <button
      class="tab-btn {activeTab === 'mods' ? 'active' : ''}"
      on:click={() => onTabChange("mods")}
    >
      Mods
    </button>

    <button
      class="tab-btn {activeTab === 'terminal' ? 'active' : ''}"
      on:click={() => onTabChange("terminal")}
    >
      Terminal
    </button>

    <button
      class="tab-btn {activeTab === 'settings' ? 'active' : ''}"
      on:click={() => onTabChange("settings")}
    >
      Settings
    </button>
  </nav>

  <div class="header-action">
    <label for="game-lang-select">Game: </label>
    <select
      id="game-lang-select"
      value={currentGameLang}
      on:change={onGameLangChange}
    >
      {#each availableGameLangs as gLang}
        <option value={gLang}>{gLang}</option>
      {/each}
    </select>

    <button class="patch-btn" on:click={onPatch} disabled={isPatching}>
      {isPatching ? "PATCHING..." : "PATCH"}
    </button>
  </div>
</header>

<style>
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px;
    border: 1px solid #000;
    background: #fff;
  }

  .nav-tabs {
    display: flex;
    gap: 4px;
  }

  .tab-btn {
    padding: 4px 8px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    cursor: pointer;
  }

  .tab-btn.active {
    background: #000;
    color: #fff;
  }

  .header-action {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
  }

  select {
    padding: 4px;
    border: 1px solid #000;
    background: #fff;
  }

  .patch-btn {
    padding: 4px 12px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-weight: bold;
    cursor: pointer;
  }
</style>
