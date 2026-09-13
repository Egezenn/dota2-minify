<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import type { Announcement } from "../types";
  import { getAnnouncementId } from "../announcements";
  import { t } from "../i18n";

  export let isOpen: boolean = false;
  export let announcements: Announcement[] = [];
  export let onDismiss: (id: string) => void;
  export let onClose: () => void;

  let currentIndex: number = 0;

  $: if (currentIndex >= announcements.length) {
    currentIndex = Math.max(0, announcements.length - 1);
  }

  $: current = announcements[currentIndex] || null;

  $: urls = current ? current.urls || (current.url ? [current.url] : []) : [];

  function handleDismiss() {
    if (!current) return;
    const id = getAnnouncementId(current);
    onDismiss(id);
  }

  function handleNext() {
    if (currentIndex < announcements.length - 1) {
      currentIndex += 1;
    }
  }

  function handlePrev() {
    if (currentIndex > 0) {
      currentIndex -= 1;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (!isOpen) return;
    if (e.key === "Escape") {
      onClose();
    } else if (e.key === "ArrowRight") {
      handleNext();
    } else if (e.key === "ArrowLeft") {
      handlePrev();
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeydown);
  });
</script>

{#if isOpen && current}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-backdrop" on:click|self={onClose}>
    <div class="modal-card">
      <div class="modal-header">
        <div class="header-title-group">
          <h3>{current.title || $t("title_announcement")}</h3>
          {#if announcements.length > 1}
            <span class="badge">({currentIndex + 1} / {announcements.length})</span>
          {/if}
        </div>
        <button class="close-btn" on:click={onClose} title={$t("button_close")}>✕</button>
      </div>

      <div class="modal-body">
        <div class="announcement-content">
          {current.text}
        </div>

        {#if urls.length > 0}
          <div class="urls-container">
            <span class="urls-label">{$t("label_related_links")}</span>
            <div class="urls-list">
              {#each urls as u}
                <a href={u} target="_blank" rel="noopener noreferrer" class="url-btn">
                  <span class="url-text">{u}</span>
                  <span class="url-icon">↗</span>
                </a>
              {/each}
            </div>
          </div>
        {/if}
      </div>

      <div class="modal-footer">
        {#if announcements.length > 1}
          <div class="nav-controls">
            <button class="btn btn-nav" on:click={handlePrev} disabled={currentIndex === 0}>
              {$t("button_previous")}
            </button>
            <button class="btn btn-nav" on:click={handleNext} disabled={currentIndex === announcements.length - 1}>
              {$t("button_next")}
            </button>
          </div>
        {/if}

        <div class="action-controls">
          <button class="btn btn-cancel" on:click={onClose}>{$t("button_close")}</button>
          <button class="btn btn-yes" on:click={handleDismiss}>{$t("button_ok")}</button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: var(--modal-backdrop, rgba(0, 0, 0, 0.5));
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
  }

  .modal-card {
    width: 500px;
    max-width: 90vw;
    max-height: 85vh;
    background: var(--modal-bg, #fff);
    border: 1px solid var(--modal-border, #000);
    display: flex;
    flex-direction: column;
    color: var(--text-primary, #000);
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-color, #000);
    background: var(--modal-bg, #fff);
  }

  .header-title-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .modal-header h3 {
    font-size: 14px;
    font-weight: bold;
    margin: 0;
  }

  .badge {
    font-size: 11px;
    color: var(--text-secondary, #666);
    font-family: inherit;
  }

  .close-btn {
    border: none;
    background: transparent;
    color: var(--text-primary, #000);
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
    line-height: 1;
  }

  .modal-body {
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
  }

  .announcement-content {
    font-size: 13px;
    color: var(--text-primary, #000);
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .urls-container {
    display: flex;
    flex-direction: column;
    gap: 6px;
    padding-top: 8px;
    border-top: 1px solid var(--border-color, #eee);
  }

  .urls-label {
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    color: var(--text-secondary, #666);
  }

  .urls-list {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .url-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    font-size: 12px;
    color: var(--text-primary, #000);
    text-decoration: none;
    background: var(--btn-bg, #fff);
    border: 1px solid var(--btn-border, #000);
    overflow: hidden;
  }

  .url-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .url-btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .url-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .url-icon {
    font-weight: bold;
    margin-left: 8px;
  }

  .modal-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 12px;
    border-top: 1px solid var(--border-color, #000);
    background: var(--modal-bg, #fff);
  }

  .nav-controls,
  .action-controls {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 26px;
    padding: 0 14px;
    border: 1px solid var(--btn-border, #000);
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    font-size: 12px;
    font-weight: bold;
    cursor: pointer;
  }

  .btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .btn-nav:hover:not(:disabled),
  .btn-cancel:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .btn-nav:active:not(:disabled),
  .btn-cancel:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .btn-yes {
    background: var(--accent, #17bebe);
    color: var(--accent-text, #000);
    border-color: var(--accent, #17bebe);
  }
</style>
