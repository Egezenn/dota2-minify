<script lang="ts">
  import type { RegistryEntry } from "../types";
  import { t } from "../i18n";

  export let entry: RegistryEntry;
  export let inProgress = false;
  export let updating = false;
  export let onInstall: (entry: RegistryEntry) => void;
  export let onUpdate: (entry: RegistryEntry) => void;
  export let onUninstall: (entry: RegistryEntry) => void;
  export let onDetails: (entry: RegistryEntry) => void;

  $: initialLetter =
    (entry.name || "?")
      .replace(/^[^a-zA-Z0-9]+/, "")
      .charAt(0)
      .toUpperCase() || "?";

  function handleImageError(event: Event) {
    const target = event.currentTarget as HTMLElement;
    if (target) target.style.display = "none";
  }
</script>

<div
  class="mod-card"
  class:active={entry.installed}
  class:incompatible={entry.installed && !entry.installed_compatible}
  role="button"
  tabindex="0"
  on:click={() => onDetails(entry)}
  on:keydown={(e) => {
    if (e.target === e.currentTarget && (e.key === "Enter" || e.key === " ")) {
      e.preventDefault();
      onDetails(entry);
    }
  }}
>
  <div class="preview-container">
    {#if entry.installed && !entry.installed_compatible}
      <span
        class="incompatible-badge"
        title={$t("community_installed_incompatible", [
          entry.installed_tag || $t("community_unknown_tag"),
          entry.current_version,
        ])}
      >
        {$t("community_incompatible_badge")}
      </span>
    {/if}
    {#if entry.preview}
      <img
        src={entry.preview}
        alt={entry.name}
        loading="lazy"
        decoding="async"
        class="preview-image"
        on:error={handleImageError}
      />
    {:else}
      <div class="preview-placeholder">
        <span class="placeholder-letter">{initialLetter}</span>
      </div>
    {/if}
  </div>

  <div class="card-footer">
    <span class="mod-name" title={entry.name}>{entry.name}</span>

    <div class="mod-actions">
      <button class="details-btn" type="button" on:click|stopPropagation={() => onDetails(entry)}>
        {$t("community_button_details")}
      </button>

      {#if entry.installed && entry.update_available}
        <button
          class="action-btn update"
          type="button"
          disabled={inProgress}
          on:click|stopPropagation={() => onUpdate(entry)}
        >
          {updating ? $t("community_button_updating") : $t("community_button_update")}
        </button>
      {:else if !entry.installed}
        <button
          class="action-btn install"
          type="button"
          disabled={inProgress || !entry.available}
          on:click|stopPropagation={() => onInstall(entry)}
        >
          {inProgress ? $t("community_button_installing") : $t("community_button_install")}
        </button>
      {/if}

      {#if entry.installed}
        <button
          class="action-btn remove"
          type="button"
          disabled={inProgress}
          on:click|stopPropagation={() => onUninstall(entry)}
        >
          {inProgress ? $t("community_button_removing") : $t("community_button_uninstall")}
        </button>
      {/if}
    </div>
  </div>
</div>

<style>
  .mod-card {
    display: flex;
    flex-direction: column;
    height: 100px;
    border: 1px solid var(--card-border, #000);
    background: var(--card-bg, #fff);
    color: var(--text-primary, #000);
    overflow: hidden;
    box-sizing: border-box;
    transition: border-color 0.15s ease;
    cursor: pointer;
  }

  .mod-card:hover {
    border-color: var(--accent, #17bebe);
  }

  .mod-card.active {
    border-color: var(--accent, #17bebe);
  }

  .mod-card.active .preview-container {
    border-bottom-color: var(--accent, #17bebe);
  }

  .mod-card.incompatible {
    border-color: var(--log-error, #ff5555);
  }

  .mod-card.incompatible .preview-container {
    border-bottom-color: var(--log-error, #ff5555);
  }

  .preview-container {
    position: relative;
    height: 60px;
    width: 100%;
    overflow: hidden;
    border-bottom: 1px solid var(--card-border, #000);
    background: var(--card-preview-bg, #f0f0f0);
    flex-shrink: 0;
  }

  .incompatible-badge {
    position: absolute;
    top: 4px;
    left: 4px;
    z-index: 1;
    padding: 1px 5px;
    border-radius: 2px;
    background: var(--log-error, #ff5555);
    color: #fff;
    font-size: 10px;
    font-weight: 700;
    line-height: 1.4;
    text-transform: uppercase;
    pointer-events: none;
  }

  .preview-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
  }

  .preview-placeholder {
    width: 100%;
    height: 100%;
    background: var(--card-preview-bg, #f0f0f0);
    display: flex;
    align-items: center;
    justify-content: center;
    user-select: none;
  }

  .placeholder-letter {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-muted, #888888);
    line-height: 1;
    text-transform: uppercase;
  }

  .card-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 40px;
    padding: 0 8px;
    gap: 6px;
    background: var(--card-footer-bg, #fff);
    flex: 1;
    box-sizing: border-box;
  }

  .mod-name {
    font-size: 12px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-primary, #000);
  }

  .mod-actions {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }

  .details-btn,
  .action-btn {
    padding: 2px 6px;
    font-size: 11px;
    line-height: 1.2;
    color: var(--btn-text, #000);
    background: var(--btn-bg, #fff);
    border: 1px solid var(--btn-border, #000);
    cursor: pointer;
    white-space: nowrap;
  }

  .details-btn:hover,
  .action-btn:hover:not(:disabled) {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .details-btn:active,
  .action-btn:active:not(:disabled) {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .action-btn.update {
    border-color: var(--accent, #17bebe);
    color: var(--accent, #17bebe);
  }

  .action-btn.remove {
    background: var(--accent, #17bebe);
    color: var(--accent-text, #000);
    border-color: var(--accent, #17bebe);
  }

  .action-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
