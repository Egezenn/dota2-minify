<script lang="ts">
  export let name: string;
  export let enabled: boolean;
  export let always: boolean = false;
  export let preview: string | null | undefined = undefined;
  export let ontoggle: (value: boolean) => void;
  export let onDetails: ((name: string) => void) | undefined = undefined;

  $: initialLetter = ((name || "").replace(/^[^a-zA-Z0-9]+/, "").charAt(0) || (name || "").charAt(0)).toUpperCase();

  function handleToggle() {
    if (always) return;
    ontoggle(!enabled);
  }

  function handleCardClick() {
    if (always) {
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
  class="mod-card {always ? 'always-mod' : ''}"
  on:click={handleCardClick}
  role="button"
  tabindex="0"
  on:keydown={(e) => (e.key === "Enter" || e.key === " ") && handleCardClick()}
>
  <div class="preview-container">
    {#if preview}
      <img src={preview} alt={name} loading="lazy" decoding="async" class="preview-image" />
    {:else}
      <div class="preview-placeholder">
        <span class="placeholder-letter">{initialLetter}</span>
      </div>
    {/if}
  </div>

  <div class="card-footer">
    <span class="mod-name" title={name}>{name}</span>

    <div class="mod-actions">
      {#if onDetails}
        <button class="details-btn" type="button" on:click={handleDetails}>
          Details
        </button>
      {/if}
      <input
        type="checkbox"
        checked={enabled || always}
        disabled={always}
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
    border: 1px solid #000;
    cursor: pointer;
    background: #fff;
    overflow: hidden;
    box-sizing: border-box;
  }

  .mod-card.always-mod {
    background: #f4f4f4;
  }

  .mod-card.always-mod .card-footer {
    background: #e8e8e8;
    opacity: 0.85;
  }

  .preview-container {
    height: 60px;
    width: 100%;
    overflow: hidden;
    border-bottom: 1px solid #000;
    background: #f0f0f0;
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
    background: #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
    user-select: none;
  }

  .placeholder-letter {
    font-size: 32px;
    font-weight: 700;
    color: #888888;
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
    background: #fff;
    flex: 1;
  }

  .mod-name {
    font-size: 12px;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #000;
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
    color: #000;
    background: #fff;
    border: 1px solid #000;
    cursor: pointer;
  }

  input[type="checkbox"] {
    cursor: pointer;
  }

  input[type="checkbox"]:disabled {
    cursor: not-allowed;
  }
</style>
