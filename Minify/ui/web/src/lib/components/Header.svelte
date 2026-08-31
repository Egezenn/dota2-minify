<script lang="ts">
  export let activeTab: string;
  export let currentGameLang: string;
  export let availableGameLangs: string[];
  export let isPatching: boolean;
  export let pluginTabs: Array<{ id: string; name: string }> = [];

  export let onTabChange: (tab: string) => void;
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

    {#each pluginTabs as plugin}
      <button
        class="tab-btn {activeTab === plugin.id ? 'active' : ''}"
        on:click={() => onTabChange(plugin.id)}
      >
        {plugin.name}
      </button>
    {/each}
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
    height: 38px;
    padding: 0 8px;
    border: 1px solid #000;
    background: #fff;
    box-sizing: border-box;
  }

  .nav-tabs {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .tab-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 8px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-size: 13px;
    font-family: inherit;
    line-height: 1;
    cursor: pointer;
    box-sizing: border-box;
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

  .header-action label {
    display: inline-flex;
    align-items: center;
    line-height: 1;
  }

  select {
    display: inline-flex;
    align-items: center;
    height: 24px;
    padding: 0 4px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-size: 13px;
    font-family: inherit;
    line-height: 1;
    box-sizing: border-box;
    cursor: pointer;
  }

  .patch-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 12px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-size: 13px;
    font-family: inherit;
    font-weight: bold;
    line-height: 1;
    cursor: pointer;
    box-sizing: border-box;
  }
</style>
