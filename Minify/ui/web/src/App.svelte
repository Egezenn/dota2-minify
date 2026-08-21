<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { modsStore } from './lib/stores/mods';
  import { localeStore } from './lib/stores/locale';
  import { resolveText } from './lib/i18n';
  import ModGrid from './lib/components/ModGrid.svelte';

  let activeTab: 'mods' | 'terminal' = 'mods';
  let logs: Array<{ text: string; type: string; timestamp?: string }> = [];
  let isPatching = false;
  let autoScroll = true;
  let terminalElement: HTMLElement | null = null;

  let availableUiLangs: string[] = [];
  let availableGameLangs: string[] = [];
  let currentGameLang = 'english';
  let initialized = false;

  $: dict = $localeStore.dict;
  $: currentLang = $localeStore.lang;

  async function loadApiData() {
    if (initialized) return;
    if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.get_current_locale) return;

    initialized = true;
    try {
      const [savedUiLang, savedGameLang, uiLangs, gameLangs] = await Promise.all([
        window.pywebview.api.get_current_locale(),
        window.pywebview.api.get_current_game_language(),
        window.pywebview.api.get_available_languages(),
        window.pywebview.api.get_available_game_languages(),
      ]);

      const targetUiLang = savedUiLang || currentLang || 'EN';
      currentGameLang = savedGameLang || 'english';
      if (Array.isArray(uiLangs) && uiLangs.length > 0) availableUiLangs = uiLangs;
      if (Array.isArray(gameLangs) && gameLangs.length > 0) availableGameLangs = gameLangs;

      const [initialLogs, patchingState, mods, locDict] = await Promise.all([
        window.pywebview.api.get_logs(),
        window.pywebview.api.is_patching(),
        window.pywebview.api.get_mods(),
        window.pywebview.api.get_localization(targetUiLang),
      ]);

      if (Array.isArray(initialLogs)) logs = initialLogs;
      isPatching = Boolean(patchingState);
      if (Array.isArray(mods)) modsStore.set(mods);
      if (locDict) localeStore.set({ lang: targetUiLang, dict: locDict });
    } catch (err) {
      console.error('Error initializing PyWebView API:', err);
    }
  }

  async function initPyWebView() {
    if (window.pywebview && window.pywebview.api && window.pywebview.api.get_current_locale) {
      await loadApiData();
      return;
    }

    window.addEventListener('pywebviewready', loadApiData, { once: true });
  }

  onMount(() => {
    (window as any).onLogReceived = (logEntry: { text: string; type: string; timestamp?: string }) => {
      logs = [...logs, logEntry];
      if (autoScroll && activeTab === 'terminal') {
        scrollToBottom();
      }
    };

    (window as any).onPatchStatusChange = (status: boolean) => {
      isPatching = status;
    };

    initPyWebView();
  });

  function getCurrentTime() {
    const now = new Date();
    return now.toTimeString().split(' ')[0];
  }

  async function scrollToBottom() {
    await tick();
    if (terminalElement) {
      terminalElement.scrollTop = terminalElement.scrollHeight;
    }
  }

  async function handlePatch() {
    if (isPatching) return;

    isPatching = true;
    activeTab = 'terminal';
    try {
      await window.pywebview.api.start_patch();
    } catch (err) {
      logs = [...logs, { text: `Error triggering patch: ${err}`, type: 'error', timestamp: getCurrentTime() }];
      isPatching = false;
    }
  }

  async function handleSaveMods(data: Record<string, boolean>) {
    try {
      await window.pywebview.api.set_mods(data);
    } catch (err) {
      console.error('Failed to save mods state:', err);
    }
  }

  async function handleLangChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const newLang = target.value;
    try {
      if (window.pywebview && window.pywebview.api) {
        const [dict] = await Promise.all([
          window.pywebview.api.get_localization(newLang),
          window.pywebview.api.set_locale(newLang),
        ]);
        localeStore.set({ lang: newLang, dict });
      } else {
        localeStore.set({ lang: newLang, dict: $localeStore.dict });
      }
    } catch (err) {
      console.error('Failed to fetch localization:', err);
    }
  }

  async function handleGameLangChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    const newGameLang = target.value;
    currentGameLang = newGameLang;
    try {
      if (window.pywebview && window.pywebview.api) {
        await window.pywebview.api.set_game_language(newGameLang);
      }
    } catch (err) {
      console.error('Failed to set game language:', err);
    }
  }

  async function handleClear() {
    logs = [];
    try {
      await window.pywebview.api.clear_logs();
    } catch (err) {
      console.error('Failed to clear logs:', err);
    }
  }
</script>

<main class="app-container">
  <header class="header">
    <div class="brand-and-tabs">
      <div class="brand">
        <span class="title">MINIFY</span>
      </div>

      <nav class="nav-tabs">
        <button
          class="tab-btn {activeTab === 'mods' ? 'active' : ''}"
          on:click={() => (activeTab = 'mods')}
        >
          {resolveText('&ui_tab_mods', [], dict) || resolveText('&button_select_mods', [], dict) || 'Mods'}
        </button>

        <button
          class="tab-btn {activeTab === 'terminal' ? 'active' : ''}"
          on:click={() => (activeTab = 'terminal')}
        >
          {resolveText('&ui_tab_terminal', [], dict) || 'Terminal'}
        </button>
      </nav>
    </div>

    <div class="header-action">
      <div class="select-group">
        <label class="lang-label" for="ui-lang-select">
          {resolveText('&ui_ui_language', [], dict) || resolveText('&language_select', [], dict) || 'UI:'}
        </label>
        <select id="ui-lang-select" value={currentLang} on:change={handleLangChange}>
          {#each availableUiLangs as lang}
            <option value={lang}>{lang}</option>
          {/each}
        </select>
      </div>

      <div class="select-group">
        <label class="lang-label" for="game-lang-select">
          {resolveText('&ui_game_language', [], dict) || 'Game:'}
        </label>
        <select id="game-lang-select" value={currentGameLang} on:change={handleGameLangChange}>
          {#each availableGameLangs as gLang}
            <option value={gLang}>{gLang}</option>
          {/each}
        </select>
      </div>

      <button class="patch-btn" on:click={handlePatch} disabled={isPatching}>
        {isPatching
          ? resolveText('&ui_status_patching', [], dict) || 'PATCHING...'
          : resolveText('&button_patch', [], dict) || 'PATCH DOTA 2'}
      </button>
    </div>
  </header>

  <section class="main-content">
    {#if activeTab === 'mods'}
      <ModGrid onSaveMods={handleSaveMods} />
    {:else if activeTab === 'terminal'}
      <div class="terminal-container">
        <div class="terminal-toolbar">
          <div>
            <span>{resolveText('&ui_tab_terminal', [], dict) || 'Terminal'}</span>
          </div>

          <div class="toolbar-controls">
            <label>
              <input type="checkbox" bind:checked={autoScroll} />
              {resolveText('&ui_auto_scroll', [], dict) || 'Auto-scroll'}
            </label>
            <button on:click={handleClear}>
              {resolveText('&ui_clear_terminal', [], dict) || 'Clear'}
            </button>
          </div>
        </div>

        <div class="terminal-body" bind:this={terminalElement}>
          {#each logs as log}
            {#if log.type === 'separator'}
              <hr />
            {:else}
              <div class="log-row">{log.text}</div>
            {/if}
          {/each}
        </div>

      </div>
    {/if}
  </section>
</main>

<style>
  .app-container {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    padding: 8px;
    gap: 8px;
  }

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

  .brand {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: bold;
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

  .main-content {
    flex: 1;
    border: 1px solid #ccc;
    overflow: hidden;
    background: #fff;
  }

  .terminal-container {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .terminal-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px;
    border-bottom: 1px solid #ccc;
    font-size: 13px;
  }

  .toolbar-controls {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .terminal-body {
    flex: 1;
    padding: 8px;
    font-family: monospace;
    font-size: 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 2px;
    user-select: text;
  }

  .log-row {
    white-space: pre-wrap;
    word-break: break-all;
    user-select: text;
  }


  hr {
    border: none;
    border-top: 1px solid #ccc;
    margin: 4px 0;
  }
</style>

