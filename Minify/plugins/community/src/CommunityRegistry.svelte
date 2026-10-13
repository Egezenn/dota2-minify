<script lang="ts">
  import { onMount } from "svelte";
  import { setPluginLocale, t } from "./lib/i18n";

  interface RegistryEntry {
    id: string;
    name: string;
    type: "mod" | "plugin" | "theme";
    repo: string;
    preview: string;
    notes_url: string;
    installed: boolean;
    installed_tag: string | null;
    latest_tag: string | null;
    update_available: boolean;
    available: boolean;
    error: string | null;
  }

  let entries: RegistryEntry[] = [];
  let selectedType = "all";
  let searchText = "";
  let loading = false;
  let activeItem = "";
  let expandedItem = "";
  let notes = "";
  let message = "";
  let errorMessage = "";
  const packageTypes = ["all", "mod", "theme", "plugin"] as const;

  $: filteredEntries = entries.filter((entry) => {
    const matchesType = selectedType === "all" || entry.type === selectedType;
    const query = searchText.trim().toLowerCase();
    return matchesType && (!query || entry.name.toLowerCase().includes(query));
  });

  async function callRegistry(action: string, params: Record<string, unknown> = {}) {
    const api = window.parent.pywebview?.api ?? window.pywebview?.api;
    if (!api?.call_plugin_api) throw new Error($t("community_error_api_unavailable"));
    const result = await api.call_plugin_api("community", action, params);
    if (result?.error) throw new Error(String(result.error));
    return result;
  }

  async function loadEntries() {
    loading = true;
    errorMessage = "";
    try {
      entries = await callRegistry("get_catalogue");
    } catch (error) {
      errorMessage = $t("community_error_catalogue", [String(error)]);
    } finally {
      loading = false;
    }
  }

  async function showNotes(entry: RegistryEntry) {
    expandedItem = expandedItem === entry.id ? "" : entry.id;
    notes = "";
    if (!expandedItem) return;
    try {
      const details = await callRegistry("get_item_details", { id: entry.id });
      notes = details?.notes || $t("community_no_notes");
    } catch (error) {
      notes = $t("community_error_notes", [String(error)]);
    }
  }

  function notifyPluginTabsChanged() {
    window.parent.postMessage({ type: "REFRESH_PLUGIN_TABS" }, "*");
  }

  function notifyModsChanged() {
    window.parent.postMessage({ type: "REFRESH_MODS" }, "*");
  }

  function notifyThemeChanged() {
    window.parent.postMessage({ type: "REFRESH_THEME" }, "*");
  }

  async function runAction(entry: RegistryEntry, action: "install_item" | "update_item" | "uninstall_item") {
    activeItem = entry.id;
    message = "";
    errorMessage = "";
    try {
      await callRegistry(action, { id: entry.id });
      const statusKey = {
        install_item: "community_status_installed",
        update_item: "community_status_updated",
        uninstall_item: "community_status_uninstalled",
      }[action];
      message = $t(statusKey, [entry.name]);
      if (entry.type === "plugin") notifyPluginTabsChanged();
      if (entry.type === "mod") notifyModsChanged();
      if (entry.type === "theme") notifyThemeChanged();
      await loadEntries();
    } catch (error) {
      const errorKey = {
        install_item: "community_error_install",
        update_item: "community_error_update",
        uninstall_item: "community_error_uninstall",
      }[action];
      errorMessage = $t(errorKey, [String(error)]);
    } finally {
      activeItem = "";
    }
  }

  onMount(() => {
    const updateLocale = (event: MessageEvent) => {
      if (event.data?.type === "LOCALE_CHANGED" && event.data.lang) {
        setPluginLocale(event.data.lang, event.data.dict || {});
      }
    };
    window.addEventListener("message", updateLocale);

    const initialize = async () => {
      try {
        const api = window.parent.pywebview?.api;
        if (api?.get_current_locale && api.get_localization) {
          const lang = await api.get_current_locale();
          const dict = await api.get_localization(lang);
          if (lang) setPluginLocale(lang, dict || {});
        }
      } catch (error) {
        console.error("Failed to load Community plugin localization:", error);
      }
      await loadEntries();
    };
    void initialize();

    return () => window.removeEventListener("message", updateLocale);
  });
</script>

<div class="registry">
  <header class="toolbar">
    <h2>{$t("community_title")}</h2>
    <div class="toolbar-actions">
      <input type="search" placeholder={$t("community_search_placeholder")} bind:value={searchText} />
      <button type="button" disabled={loading} on:click={loadEntries}>
        {loading ? $t("community_button_loading") : $t("community_button_refresh")}
      </button>
    </div>
  </header>

  <nav class="filters" aria-label="Package type">
    {#each packageTypes as type}
      <button type="button" class:active={selectedType === type} on:click={() => (selectedType = type)}>
        {$t(`community_filter_${type === "all" ? "all" : `${type}s`}`)}
      </button>
    {/each}
  </nav>

  {#if message}<p class="notice">{message}</p>{/if}
  {#if errorMessage}<p class="error" role="alert">{errorMessage}</p>{/if}

  <main class="catalogue">
    {#if loading && entries.length === 0}
      <p class="empty">{$t("community_loading_packages")}</p>
    {:else if filteredEntries.length === 0 && !errorMessage}
      <p class="empty">{$t("community_no_packages")}</p>
    {:else if filteredEntries.length > 0}
      <div class="cards">
        {#each filteredEntries as entry (entry.id)}
          <article class="entry">
            {#if entry.preview}
              <a class="preview" href={entry.preview} target="_blank" rel="noreferrer">
                <img src={entry.preview} alt={`${entry.name} preview`} loading="lazy" />
              </a>
            {/if}
            <div class="entry-content">
              <div class="entry-heading">
                <h3>{entry.name}</h3>
                <span class="type">{$t(`community_type_${entry.type}`)}</span>
              </div>
              <p class="release">
                {#if entry.installed}
                  {$t("community_installed_tag", [entry.installed_tag || $t("community_unknown_tag")])}
                {:else}
                  {$t("community_latest_tag", [entry.latest_tag || $t("community_unavailable_tag")])}
                {/if}
              </p>
              {#if entry.installed && entry.update_available}
                <p class="update-label">{$t("community_update_available", [entry.latest_tag || ""])}</p>
              {/if}
              {#if entry.error}
                <p class="error entry-error">{entry.error}</p>
              {/if}
              <div class="entry-actions">
                {#if entry.installed && entry.update_available}
                  <button
                    type="button"
                    class="primary"
                    disabled={activeItem === entry.id}
                    on:click={() => runAction(entry, "update_item")}
                  >
                    {activeItem === entry.id ? $t("community_button_updating") : $t("community_button_update")}
                  </button>
                {:else if !entry.installed}
                  <button
                    type="button"
                    class="primary"
                    disabled={!entry.available || activeItem === entry.id}
                    on:click={() => runAction(entry, "install_item")}
                  >
                    {activeItem === entry.id ? $t("community_button_installing") : $t("community_button_install")}
                  </button>
                {/if}
                {#if entry.installed}
                  <button
                    type="button"
                    disabled={activeItem === entry.id}
                    on:click={() => runAction(entry, "uninstall_item")}
                  >
                    {$t("community_button_uninstall")}
                  </button>
                {/if}
                <button type="button" on:click={() => showNotes(entry)}>
                  {expandedItem === entry.id ? $t("community_button_hide_details") : $t("community_button_details")}
                </button>
                <a href={entry.repo} target="_blank" rel="noreferrer">{$t("community_button_repository")}</a>
              </div>
              {#if expandedItem === entry.id}
                <pre class="notes">{notes || $t("community_loading_details")}</pre>
              {/if}
            </div>
          </article>
        {/each}
      </div>
    {/if}
  </main>
</div>

<style>
  :global(html),
  :global(body) {
    width: 100%;
    height: 100%;
    margin: 0;
    overflow: hidden;
    background: transparent;
    color: var(--text-primary, #e0e0e0);
    font: 13px var(--font-sans, system-ui, sans-serif);
  }

  .registry {
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100vh;
    background: transparent;
  }

  .toolbar,
  .filters,
  .entry-heading,
  .entry-actions,
  .toolbar-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .toolbar {
    justify-content: space-between;
    min-height: 42px;
    padding: 0 10px;
    border-bottom: 1px solid var(--border-color, #333);
    background: var(--bg-secondary, #1a1a1a);
  }

  h2,
  h3,
  p {
    margin: 0;
  }

  h2 {
    font-size: 15px;
  }

  .toolbar-actions input {
    width: min(260px, 35vw);
    height: 26px;
    padding: 0 8px;
    border: 1px solid var(--input-border, #333);
    border-radius: 0;
    background: var(--input-bg, #1a1a1a);
    color: var(--input-text, #e0e0e0);
  }

  button,
  .entry-actions a {
    padding: 5px 9px;
    border: 1px solid var(--btn-border, #333);
    border-radius: 0;
    background: var(--btn-bg, #1e1e1e);
    color: var(--btn-text, #e0e0e0);
    font: inherit;
    text-decoration: none;
    cursor: pointer;
  }

  button:hover:not(:disabled),
  .entry-actions a:hover {
    background: var(--btn-hover-bg, #282828);
    border-color: var(--btn-hover-border, var(--accent, #17bebe));
  }

  button:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }

  .filters {
    min-height: 42px;
    padding: 0 10px;
    border-bottom: 1px solid var(--border-color, #333);
  }

  .filters button.active,
  button.primary {
    background: var(--accent, #17bebe);
    color: var(--accent-text, #000);
    border-color: var(--accent, #17bebe);
  }

  .catalogue {
    flex: 1;
    overflow: auto;
    padding: 12px;
  }

  .cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    align-items: start;
    gap: 12px;
  }

  .entry {
    overflow: hidden;
    border: 1px solid var(--card-border, #333);
    border-radius: 10px;
    background: var(--card-bg, #181818);
  }

  .preview {
    display: block;
    height: 150px;
    background: var(--card-preview-bg, #141414);
    text-align: center;
  }

  .preview img {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .entry-content {
    display: grid;
    gap: 8px;
    padding: 10px;
  }

  .entry-heading {
    justify-content: space-between;
  }

  .entry-heading h3 {
    font-size: 14px;
  }

  .type {
    padding: 2px 7px;
    border: 1px solid var(--border-color, #333);
    border-radius: 999px;
    color: var(--text-secondary, #aaa);
    text-transform: capitalize;
  }

  .release,
  .update-label,
  .empty {
    color: var(--text-secondary, #aaa);
  }

  .update-label {
    color: var(--accent, #17bebe);
  }

  .entry-actions {
    flex-wrap: wrap;
  }

  .notes {
    overflow: auto;
    max-height: 220px;
    margin: 0;
    padding: 8px;
    border-radius: 6px;
    background: var(--terminal-bg, #0c0d0e);
    color: var(--terminal-text, #d4d4d4);
    font: 12px/1.45 var(--font-mono, monospace);
    white-space: pre-wrap;
  }

  .notice,
  .error {
    margin: 8px 12px 0;
    color: var(--accent, #17bebe);
  }

  .error {
    color: var(--log-error, #ff5555);
  }

  .entry-error {
    margin: 0;
    font-size: 12px;
  }

  .empty {
    padding: 20px;
    text-align: center;
  }
</style>
