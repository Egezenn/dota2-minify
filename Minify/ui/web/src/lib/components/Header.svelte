<script lang="ts">
  import { t } from "../i18n";
  import ghIcon from "../../assets/github.svg";
  import wikiIcon from "../../assets/wiki.ico";
  import discordIcon from "../../assets/discord.svg";
  import telegramIcon from "../../assets/telegram.png";
  import bmcIcon from "../../assets/buymeacoffee.svg";

  export let activeTab: string;
  export let isPatching: boolean;
  export let pluginTabs: Array<{ id: string; name: string }> = [];

  export let onTabChange: (tab: string) => void;
  export let onPatch: () => void;
  export let onUninstallClick: () => void;

  function openExternal(url: string) {
    if (window.pywebview?.api?.open_url) {
      window.pywebview.api.open_url(url);
    } else {
      window.open(url, "_blank");
    }
  }
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
    <div class="header-links">
      <button
        type="button"
        class="header-link-btn"
        on:click={() => openExternal("https://egezenn.github.io/dota2-minify")}
        title="GitHub IO"
        aria-label="GitHub IO"
      >
        <img src={ghIcon} alt="GitHub IO" class="header-link-icon gh-icon" />
      </button>

      <button
        type="button"
        class="header-link-btn"
        on:click={() => openExternal("https://github.com/egezenn/dota2-minify/wiki")}
        title="GitHub Wiki"
        aria-label="GitHub Wiki"
      >
        <img src={wikiIcon} alt="GitHub Wiki" class="header-link-icon" />
      </button>

      <button
        type="button"
        class="header-link-btn"
        on:click={() => openExternal("https://discord.com/invite/9867CPv7cy")}
        title="Discord"
        aria-label="Discord"
      >
        <img src={discordIcon} alt="Discord" class="header-link-icon" />
      </button>

      <button
        type="button"
        class="header-link-btn"
        on:click={() => openExternal("https://t.me/dota2minify")}
        title="Telegram"
        aria-label="Telegram"
      >
        <img src={telegramIcon} alt="Telegram" class="header-link-icon" />
      </button>

      <button
        type="button"
        class="header-link-btn"
        on:click={() => openExternal("https://buymeacoffee.com/egezenn")}
        title="BuyMeACoffee"
        aria-label="BuyMeACoffee"
      >
        <img src={bmcIcon} alt="BuyMeACoffee" class="header-link-icon" />
      </button>
    </div>

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

  .header-links {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-right: 2px;
  }

  .header-link-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    border: 1px solid var(--btn-border, #000);
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    cursor: pointer;
    box-sizing: border-box;
  }

  .header-link-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
    color: var(--accent, #17bebe);
  }

  .header-link-btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .header-link-icon {
    width: 14px;
    height: 14px;
    object-fit: contain;
    display: block;
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
