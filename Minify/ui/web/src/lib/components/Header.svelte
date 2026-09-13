<script lang="ts">
  import { t } from "../i18n";

  export let activeTab: string;
  export let isPatching: boolean;
  export let pluginTabs: Array<{ id: string; name: string }> = [];

  export let onTabChange: (tab: string) => void;
  export let onPatch: () => void;
  export let onUninstallClick: () => void;
</script>

<header class="header">
  <nav class="nav-tabs">
    <button class="tab-btn {activeTab === 'mods' ? 'active' : ''}" on:click={() => onTabChange("mods")}>
      {$t("tab_mods")}
    </button>

    <button class="tab-btn {activeTab === 'terminal' ? 'active' : ''}" on:click={() => onTabChange("terminal")}>
      {$t("tab_terminal")}
    </button>

    <button class="tab-btn {activeTab === 'settings' ? 'active' : ''}" on:click={() => onTabChange("settings")}>
      {$t("tab_settings")}
    </button>

    {#each pluginTabs as plugin}
      <button class="tab-btn {activeTab === plugin.id ? 'active' : ''}" on:click={() => onTabChange(plugin.id)}>
        {$t(plugin.name)}
      </button>
    {/each}
  </nav>

  <div class="header-action">
    <button class="uninstall-btn" on:click={onUninstallClick} disabled={isPatching}>
      {$t("button_uninstall")}
    </button>
    <button class="patch-btn" on:click={onPatch} disabled={isPatching}>
      {isPatching ? $t("button_patching") : $t("button_patch")}
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
    border: 1px solid var(--border-color, #000);
    background: var(--bg-primary, #fff);
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
    border: 1px solid var(--btn-border, #000);
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    font-size: 13px;
    font-family: inherit;
    line-height: 1;
    cursor: pointer;
    box-sizing: border-box;
  }

  .tab-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .tab-btn.active {
    background: var(--accent, #17bebe);
    color: var(--accent-text, #000);
    border-color: var(--accent, #17bebe);
  }

  .header-action {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-primary, #000);
  }

  .uninstall-btn,
  .patch-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 12px;
    border: 1px solid var(--btn-border, #000);
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    font-size: 13px;
    font-family: inherit;
    font-weight: bold;
    line-height: 1;
    cursor: pointer;
    box-sizing: border-box;
  }

  .uninstall-btn:hover,
  .patch-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .uninstall-btn:active,
  .patch-btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }
</style>
