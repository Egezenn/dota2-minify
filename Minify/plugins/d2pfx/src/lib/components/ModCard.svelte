<script lang="ts">
  import type { D2Mod } from "../types";

  export let mod: D2Mod;
  export let installed: boolean = false;
  export let inProgress: boolean = false;
  export let enabled: boolean = false;
  export let onInstall: (mod: D2Mod) => void;
  export let onUninstall: (mod: D2Mod) => void;
  export let onToggleEnabled: ((mod: D2Mod, enabled: boolean) => void) | undefined = undefined;

  function formatAuthors(author: any, sender: any): string {
    const parts: string[] = [];
    if (author) {
      if (Array.isArray(author)) parts.push(`By: ${author.join(", ")}`);
      else parts.push(`By: ${author}`);
    }
    if (sender) {
      if (Array.isArray(sender)) parts.push(`Sender: ${sender.join(", ")}`);
      else parts.push(`Sender: ${sender}`);
    }
    return parts.join(" | ");
  }

  function formatTags(tags: any): string {
    if (!tags) return "";
    if (Array.isArray(tags)) return tags.join(", ");
    if (typeof tags === "object") return Object.keys(tags).filter((k) => tags[k]).join(", ");
    return String(tags);
  }

  function handleImageError(event: Event) {
    const target = event.currentTarget as HTMLElement;
    if (target) {
      target.style.display = "none";
    }
  }
</script>

<div class="mod-card">
  <div class="preview-box">
    {#if mod.preview_url}
      <img
        src={mod.preview_url}
        alt={mod.name}
        loading="lazy"
        decoding="async"
        class="preview-img"
        on:error={handleImageError}
      />
    {:else}
      <span class="no-preview">NO PREVIEW</span>
    {/if}
  </div>

  <div class="card-details">
    <div class="mod-title">
      {mod.name}{mod.label ? ` (${mod.label})` : ""}
    </div>

    {#if formatAuthors(mod.author, mod.sender)}
      <div class="mod-meta">
        {formatAuthors(mod.author, mod.sender)}
      </div>
    {/if}

    {#if formatTags(mod.tags)}
      <div class="mod-tags">
        {formatTags(mod.tags)}
      </div>
    {/if}
  </div>

  <div class="card-actions">
    {#if installed}
      <label class="checkbox-container" title={enabled ? "Disable mod" : "Enable mod"}>
        <input
          type="checkbox"
          checked={enabled}
          disabled={inProgress}
          on:change={(e) => onToggleEnabled && onToggleEnabled(mod, e.currentTarget.checked)}
        />
      </label>
      <button
        class="install-btn installed"
        disabled={inProgress}
        on:click={() => onUninstall(mod)}
      >
        {inProgress ? "REMOVING..." : "REMOVE"}
      </button>
    {:else if inProgress}
      <label class="checkbox-container" title={enabled ? "Disable mod" : "Enable mod"}>
        <input
          type="checkbox"
          checked={enabled}
          on:change={(e) => onToggleEnabled && onToggleEnabled(mod, e.currentTarget.checked)}
        />
      </label>
      <button class="install-btn" disabled>
        INSTALLING...
      </button>
    {:else}
      <button
        class="install-btn"
        disabled={inProgress}
        on:click={() => onInstall(mod)}
      >
        INSTALL
      </button>
    {/if}
  </div>
</div>

<style>
  .mod-card {
    border: 1px solid #000;
    padding: 8px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    background: #fff;
  }

  .preview-box {
    width: 100%;
    height: 100px;
    border: 1px solid #000;
    background: #f8f8f8;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    margin-bottom: 6px;
  }

  .preview-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .no-preview {
    font-size: 10px;
    color: #888;
  }

  .card-details {
    flex: 1;
    margin-bottom: 6px;
  }

  .mod-title {
    font-weight: bold;
    font-size: 12px;
    margin-bottom: 2px;
    line-height: 1.2;
  }

  .mod-meta {
    font-size: 10px;
    color: #555;
    margin-bottom: 2px;
  }

  .mod-tags {
    font-size: 9px;
    color: #0055bb;
    word-break: break-all;
  }

  .card-actions {
    margin-top: 4px;
    display: flex;
    gap: 4px;
  }

  .install-btn {
    flex: 1;
    min-width: 0;
    padding: 4px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-weight: bold;
    cursor: pointer;
    font-size: 11px;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .install-btn.installed {
    background: #000;
    color: #fff;
  }

  .install-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .checkbox-container {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    border: 1px solid #000;
    background: #fff;
    cursor: pointer;
    flex-shrink: 0;
  }

  .checkbox-container input[type="checkbox"] {
    cursor: pointer;
    margin: 0;
    width: 14px;
    height: 14px;
    accent-color: #000;
  }

  .checkbox-container:has(input:disabled) {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
