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
  <div class="brand-and-tabs">
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
  </div>

  <div class="header-action">
    <div class="select-group">
      <label class="lang-label" for="game-lang-select"> Game: </label>
      <select
        id="game-lang-select"
        value={currentGameLang}
        on:change={onGameLangChange}
      >
        {#each availableGameLangs as gLang}
          <option value={gLang}>{gLang}</option>
        {/each}
      </select>
    </div>

    <button class="patch-btn" on:click={onPatch} disabled={isPatching}>
      {isPatching ? "PATCHING..." : "PATCH DOTA 2"}
    </button>
  </div>
</header>

<style>
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px;
    border: 1px solid #ccc;
    background: #fff;
  }

  .brand-and-tabs {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .nav-tabs {
    display: flex;
    gap: 4px;
  }

  .tab-btn {
    padding: 4px 8px;
    border: 1px solid #ccc;
    background: #f0f0f0;
    cursor: pointer;
  }

  .tab-btn.active {
    background: #fff;
    font-weight: bold;
    border-bottom-color: transparent;
  }

  .header-action {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .select-group {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .lang-label {
    font-size: 12px;
    font-weight: 600;
  }

  .patch-btn {
    padding: 6px 12px;
    font-weight: bold;
    cursor: pointer;
  }
</style>
