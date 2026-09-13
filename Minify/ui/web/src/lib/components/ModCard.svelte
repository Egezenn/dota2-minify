<script lang="ts">
  import { t } from "../i18n";
  export let name: string;
  export let displayName: string = "";
  export let enabled: boolean;
  export let always: boolean = false;
  export let untickable: boolean = false;
  export let preview: string | null | undefined = undefined;
  export let ontoggle: (value: boolean) => void;
  export let onDetails: ((name: string) => void) | undefined = undefined;

  $: effectiveName = displayName || name;
  $: initialLetter = (
    (effectiveName || "").replace(/^[^a-zA-Z0-9]+/, "").charAt(0) || (effectiveName || "").charAt(0)
  ).toUpperCase();

  function handleToggle() {
    if (always || untickable) return;
    ontoggle(!enabled);
  }

  function handleCardClick() {
    if (always || untickable) {
      if (onDetails) onDetails(name);
    } else {
      handleToggle();
    }
  }

  function handleDetails(e: MouseEvent) {
    e.stopPropagation();
    if (onDetails) {
      onDetails(name);
    }
  }
</script>

<div
  class="mod-card {always ? 'always-mod' : ''} {untickable ? 'untickable-mod' : ''}"
  class:active={!untickable && (enabled || always)}
  on:click={handleCardClick}
  role="button"
  tabindex="0"
  on:keydown={(e) => (e.key === "Enter" || e.key === " ") && handleCardClick()}
>
  <div class="preview-container">
    {#if preview}
      <img src={preview} alt={effectiveName} loading="lazy" decoding="async" class="preview-image" />
    {:else}
      <div class="preview-placeholder">
        <span class="placeholder-letter">{initialLetter}</span>
      </div>
    {/if}
  </div>

  <div class="card-footer">
    <span class="mod-name" title={effectiveName}>{effectiveName}</span>

    <div class="mod-actions">
      {#if onDetails}
        <button class="details-btn" type="button" on:click={handleDetails}>
          {$t("button_details")}
        </button>
      {/if}
      <input
        type="checkbox"
        checked={!untickable && (enabled || always)}
        disabled={always || untickable}
        on:change={handleToggle}
        on:click|stopPropagation
      />
    </div>
  </div>
</div>

<style>
  .mod-card {
    display: flex;
    flex-direction: column;
    height: 100px;
    border: 1px solid var(--card-border, #000);
    cursor: pointer;
    background: var(--card-bg, #fff);
    color: var(--text-primary, #000);
    overflow: hidden;
    box-sizing: border-box;
    transition: border-color 0.15s ease;
  }

  .mod-card.active {
    border-color: var(--accent, #17bebe);
  }

  .mod-card.active .preview-container {
    border-bottom-color: var(--accent, #17bebe);
  }

  .mod-card.always-mod {
    background: var(--bg-secondary, #f4f4f4);
  }

  .mod-card.always-mod .card-footer {
    background: var(--bg-tertiary, #e8e8e8);
    opacity: 0.85;
  }

  .mod-card.untickable-mod {
    opacity: 0.6;
    cursor: default;
  }

  .mod-card.untickable-mod .card-footer {
    opacity: 0.85;
  }

  .preview-container {
    height: 60px;
    width: 100%;
    overflow: hidden;
    border-bottom: 1px solid var(--card-border, #000);
    background: var(--card-preview-bg, #f0f0f0);
    flex-shrink: 0;
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
    gap: 6px;
    flex-shrink: 0;
  }

  .details-btn {
    padding: 2px 6px;
    font-size: 11px;
    color: var(--btn-text, #000);
    background: var(--btn-bg, #fff);
    border: 1px solid var(--btn-border, #000);
    cursor: pointer;
  }

  .details-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .details-btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  input[type="checkbox"] {
    cursor: pointer;
  }

  input[type="checkbox"]:disabled {
    cursor: not-allowed;
  }
</style>
