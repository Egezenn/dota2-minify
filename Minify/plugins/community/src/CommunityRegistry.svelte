<script lang="ts">
  import { onMount } from "svelte";
  import { setPluginLocale, t } from "./lib/i18n";
  import type { RegistryEntry } from "./lib/types";
  import ModCard from "./lib/components/ModCard.svelte";
  import ModDetailsModal from "./lib/components/ModDetailsModal.svelte";

  let entries: RegistryEntry[] = [];
  let selectedType = "all";
  let searchText = "";
  let loading = false;
  let activeItem = "";
  let selectedEntry: RegistryEntry | null = null;
  let notes = "";
  let notesLoading = false;
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

  async function openDetails(entry: RegistryEntry) {
    selectedEntry = entry;
    notes = "";
    notesLoading = true;
    try {
      const details = await callRegistry("get_item_details", { id: entry.id });
      notes = details?.notes || "";
    } catch (error) {
      notes = $t("community_error_notes", [String(error)]);
    } finally {
      notesLoading = false;
    }
  }

  function closeDetails() {
    selectedEntry = null;
    notes = "";
    notesLoading = false;
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
    errorMessage = "";
    try {
      await callRegistry(action, { id: entry.id });
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

  <main class="catalogue">
    {#if loading && entries.length === 0}
      <p class="empty">{$t("community_loading_packages")}</p>
    {:else if filteredEntries.length === 0 && !errorMessage}
      <p class="empty">{$t("community_no_packages")}</p>
    {:else if filteredEntries.length > 0}
      <div class="mod-grid">
        {#each filteredEntries as entry (entry.id)}
          <ModCard
            {entry}
            inProgress={activeItem === entry.id}
            updating={activeItem === entry.id}
            onInstall={(e) => runAction(e, "install_item")}
            onUpdate={(e) => runAction(e, "update_item")}
            onUninstall={(e) => runAction(e, "uninstall_item")}
            onDetails={openDetails}
          />
        {/each}
      </div>
    {/if}
  </main>

  <ModDetailsModal entry={selectedEntry} {notes} loading={notesLoading} onClose={closeDetails} />
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

  button {
    padding: 5px 9px;
    border: 1px solid var(--btn-border, #333);
    border-radius: 0;
    background: var(--btn-bg, #1e1e1e);
    color: var(--btn-text, #e0e0e0);
    font: inherit;
    cursor: pointer;
  }

  button:hover:not(:disabled) {
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

  .filters button.active {
    background: var(--accent, #17bebe);
    color: var(--accent-text, #000);
    border-color: var(--accent, #17bebe);
  }

  .catalogue {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }

  .mod-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    align-content: start;
    gap: 8px;
  }

  .empty {
    padding: 20px;
    text-align: center;
    color: var(--text-secondary, #aaa);
  }
</style>
