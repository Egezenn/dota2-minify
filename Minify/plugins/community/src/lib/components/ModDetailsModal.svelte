<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { marked } from "marked";
  import markedAlert from "marked-alert";
  import type { RegistryEntry } from "../types";
  import { t } from "../i18n";

  export let entry: RegistryEntry | null = null;
  export let notes = "";
  export let loading = false;
  export let onClose: () => void;

  let previewLightboxOpen = false;

  marked.setOptions({ gfm: true, breaks: true });
  marked.use(markedAlert());

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      if (previewLightboxOpen) {
        e.preventDefault();
        e.stopPropagation();
        previewLightboxOpen = false;
      } else {
        onClose();
      }
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeyDown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeyDown);
  });

  function formatNotes(markdown: string): string {
    if (!markdown) return "";
    return marked.parse(markdown) as string;
  }
</script>

{#if entry}
  <div
    class="modal-backdrop"
    on:click={onClose}
    role="button"
    tabindex="-1"
    on:keydown={(e) => {
      if (e.key === "Escape" && !previewLightboxOpen) {
        onClose();
      }
    }}
  >
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <div class="modal-card" on:click|stopPropagation role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <header class="modal-header">
        <h2 id="modal-title">{entry.name}</h2>
        <button class="close-btn" type="button" on:click={onClose} aria-label={$t("community_button_close")}>
          &times;
        </button>
      </header>

      <div class="modal-body">
        <div class="modal-meta">
          <span class="type">{$t(`community_type_${entry.type}`)}</span>
          {#if entry.installed}
            <span>{$t("community_installed_tag", [entry.installed_tag || $t("community_unknown_tag")])}</span>
          {:else}
            <span>{$t("community_latest_tag", [entry.latest_tag || $t("community_unavailable_tag")])}</span>
          {/if}
          {#if entry.installed && !entry.installed_compatible}
            <span class="incompatible">
              {$t("community_installed_incompatible", [
                entry.installed_tag || $t("community_unknown_tag"),
                entry.current_version,
              ])}
            </span>
          {/if}
          {#if entry.installed && entry.update_available}
            <span class="update-label">{$t("community_update_available", [entry.latest_tag || ""])}</span>
          {/if}
          {#if entry.error}
            <span class="entry-error">{entry.error}</span>
          {/if}
          {#if entry.repo}
            <a href={entry.repo} target="_blank" rel="noreferrer">{$t("community_button_repository")}</a>
          {/if}
        </div>

        {#if loading}
          <div class="loading-state">{$t("community_loading_details")}</div>
        {:else if entry.preview || notes}
          <div class="mod-overview" class:has-both={entry.preview && notes}>
            {#if entry.preview}
              <div class="image-wrapper">
                <button
                  type="button"
                  class="image-preview-btn"
                  on:click={() => (previewLightboxOpen = true)}
                  title={$t("community_title_click_to_preview")}
                  aria-label={$t("community_title_click_to_preview")}
                >
                  <img src={entry.preview} alt={`${$t("community_label_preview")} - ${entry.name}`} />
                </button>
              </div>
            {/if}

            {#if notes}
              <div class="notes-content">{@html formatNotes(notes)}</div>
            {/if}
          </div>
        {:else}
          <div class="empty-state">{$t("community_no_notes")}</div>
        {/if}
      </div>

      <footer class="modal-footer">
        <button class="btn-close" type="button" on:click={onClose}>{$t("community_button_close")}</button>
      </footer>
    </div>
  </div>

  {#if previewLightboxOpen && entry.preview}
    <div
      class="lightbox-backdrop"
      on:click|stopPropagation={() => (previewLightboxOpen = false)}
      role="button"
      tabindex="-1"
      on:keydown={(e) => {
        if (e.key === "Escape") {
          e.stopPropagation();
          e.preventDefault();
          previewLightboxOpen = false;
        }
      }}
    >
      <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <div class="lightbox-card" on:click|stopPropagation role="dialog" aria-modal="true" aria-label="Image Preview">
        <header class="lightbox-header">
          <span class="lightbox-title">{entry.name} - {$t("community_label_preview")}</span>
          <button
            class="close-btn"
            type="button"
            on:click|stopPropagation={() => (previewLightboxOpen = false)}
            aria-label={$t("community_button_close")}
          >
            &times;
          </button>
        </header>
        <div
          class="lightbox-body"
          role="button"
          tabindex="-1"
          on:click|stopPropagation={() => (previewLightboxOpen = false)}
          on:keydown={(e) => {
            if (e.key === "Enter" || e.key === " " || e.key === "Escape") {
              e.stopPropagation();
              e.preventDefault();
              previewLightboxOpen = false;
            }
          }}
          title={$t("community_title_click_to_preview")}
        >
          <img src={entry.preview} alt={`${$t("community_label_preview")} - ${entry.name}`} />
        </div>
      </div>
    </div>
  {/if}
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: var(--modal-backdrop, rgba(0, 0, 0, 0.5));
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-card {
    --modal-height: 80vh;
    background: var(--modal-bg, #fff);
    width: 80vw;
    height: var(--modal-height);
    border: 1px solid var(--modal-border, #000);
    display: flex;
    flex-direction: column;
    color: var(--text-primary, #000);
    container-type: size;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 38px;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border-color, #000);
    box-sizing: border-box;
  }

  .modal-header h2 {
    font-size: 15px;
    font-weight: bold;
    margin: 0;
    line-height: 1.2;
  }

  .close-btn {
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    border: 1px solid var(--btn-border, #000);
    padding: 2px 8px;
    cursor: pointer;
  }

  .close-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .close-btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .modal-body {
    padding: 24px 32px;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }

  .modal-meta {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px 12px;
    font-size: 12px;
    color: var(--text-secondary, #666);
  }

  .modal-meta a {
    color: var(--accent, #17bebe);
  }

  .modal-meta .type {
    text-transform: capitalize;
  }

  .modal-meta .incompatible,
  .modal-meta .entry-error {
    color: var(--log-error, #ff5555);
  }

  .modal-meta .update-label {
    color: var(--accent, #17bebe);
  }

  .loading-state,
  .empty-state {
    padding: 24px;
    text-align: center;
    font-size: 13px;
    color: var(--text-secondary, #666);
  }

  .mod-overview {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  @container (min-width: 700px) {
    .mod-overview.has-both {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-items: start;
      gap: 16px;
    }

    .mod-overview.has-both > * {
      min-width: 0;
    }
  }

  @media (min-width: 900px) {
    .mod-overview.has-both {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-items: start;
      gap: 16px;
    }

    .mod-overview.has-both > * {
      min-width: 0;
    }
  }

  .image-wrapper {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  .image-preview-btn {
    background: transparent;
    border: none;
    padding: 0;
    cursor: zoom-in;
    display: inline-flex;
    justify-content: center;
    max-width: 100%;
  }

  .image-preview-btn:hover img {
    border-color: var(--accent, #17bebe);
  }

  .image-wrapper img {
    max-width: 100%;
    max-height: 58vh;
    object-fit: contain;
    display: block;
    border: 1px solid var(--border-color, #000);
  }

  .lightbox-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .lightbox-card {
    background: var(--modal-bg, #fff);
    border: 1px solid var(--modal-border, #000);
    display: flex;
    flex-direction: column;
    max-width: 92vw;
    max-height: 92vh;
    box-sizing: border-box;
  }

  .lightbox-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 38px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--border-color, #000);
    background: var(--modal-bg, #fff);
    gap: 12px;
    box-sizing: border-box;
  }

  .lightbox-title {
    font-size: 13px;
    font-weight: bold;
    color: var(--text-primary, #000);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .lightbox-body {
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: 12px;
    background: var(--terminal-bg, var(--bg-primary, #000));
    cursor: zoom-out;
  }

  .lightbox-body img {
    max-width: 88vw;
    max-height: 80vh;
    object-fit: contain;
    display: block;
  }

  .notes-content {
    width: 100%;
    border: 1px solid var(--border-color, #000);
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #000);
    padding: 16px 20px;
    font-size: 13px;
    line-height: 1.5;
    overflow-wrap: break-word;
  }

  .notes-content :global(.markdown-alert) {
    border: 1px solid var(--border-color, #000);
    border-left: 4px solid var(--border-color, #000);
    padding: 6px 10px;
    margin: 6px 0;
    background: var(--bg-secondary, #fff);
    color: var(--text-primary, #000);
  }

  .notes-content :global(.markdown-alert-title) {
    font-weight: bold;
    font-size: 12px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .notes-content :global(p) {
    margin-bottom: 0.75em;
  }

  .notes-content :global(p:last-child) {
    margin-bottom: 0;
  }

  .notes-content :global(h1),
  .notes-content :global(h2),
  .notes-content :global(h3) {
    font-size: 14px;
    font-weight: bold;
    margin-top: 12px;
    margin-bottom: 6px;
  }

  .notes-content :global(ul),
  .notes-content :global(ol) {
    padding-left: 20px;
    margin-top: 4px;
    margin-bottom: 8px;
  }

  .notes-content :global(pre) {
    border: 1px solid var(--border-color, #000);
    padding: 8px 12px;
    margin: 6px 0;
    background: var(--bg-secondary, #f8f9fa);
    color: var(--text-primary, #000);
    overflow-x: auto;
  }

  .notes-content :global(pre code) {
    border: none;
    padding: 0;
    background: transparent;
    white-space: pre;
  }

  .notes-content :global(code) {
    border: 1px solid var(--border-color, #000);
    padding: 1px 4px;
    font-family: monospace;
    font-size: 12px;
    background: var(--bg-secondary, transparent);
    color: var(--text-primary, inherit);
  }

  .modal-footer {
    padding: 8px 12px;
    border-top: 1px solid var(--border-color, #000);
    background: var(--modal-bg, #fff);
    display: flex;
    justify-content: flex-end;
  }

  .btn-close {
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    border: 1px solid var(--btn-border, #000);
    padding: 4px 12px;
    cursor: pointer;
  }

  .btn-close:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }
</style>
