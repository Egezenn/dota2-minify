<script lang="ts">
  import { t } from "../i18n";

  export let isOpen: boolean = false;
  export let onIgnore: () => void;
  export let onLater: () => void;
  export let onSuccess: () => void;

  let isDownloading = false;
  let errorMessage = "";

  async function handleDownload() {
    isDownloading = true;
    errorMessage = "";
    try {
      const api = window.pywebview?.api;
      const downloadFn = api?.download_workshop_tools;
      const success = await downloadFn?.();
      if (success) {
        onSuccess();
      } else {
        errorMessage = "Download or extraction failed. Check Terminal for details.";
      }
    } catch (err) {
      errorMessage = String(err);
    } finally {
      isDownloading = false;
    }
  }

  function handleIgnore() {
    if (isDownloading) return;
    onIgnore();
  }

  function handleLater() {
    if (isDownloading) return;
    onLater();
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-backdrop" on:click|self={handleLater}>
    <div class="modal-card">
      <div class="modal-header">
        <h3>
          {$t("title_download_workshop_tools")}
        </h3>
        {#if !isDownloading}
          <button class="close-btn" on:click={handleLater} title={$t("button_close")}>✕</button>
        {/if}
      </div>

      <div class="modal-body">
        <p class="modal-text">
          {$t("modal_workshop_tools_download_prompt")}
        </p>

        <div class="repo-link-box">
          <a
            href="https://github.com/Dota-Modding-Community/workshoptools/releases"
            target="_blank"
            rel="noopener noreferrer"
            class="repo-link"
          >
            https://github.com/Dota-Modding-Community/workshoptools/releases
          </a>
        </div>

        {#if errorMessage}
          <p class="error-text">{errorMessage}</p>
        {/if}
      </div>

      <div class="modal-footer">
        {#if isDownloading}
          <div class="status-msg-running">{$t("status_downloading")}</div>
          <button class="btn btn-yes" disabled>{$t("status_downloading")}</button>
        {:else if errorMessage}
          <button class="btn btn-cancel" on:click={handleLater}>{$t("button_close")}</button>
          <div class="action-controls">
            <button class="btn btn-yes" on:click={handleDownload}>{$t("button_retry")}</button>
          </div>
        {:else}
          <button class="btn btn-cancel" on:click={handleIgnore}>
            {$t("button_ignore")}
          </button>
          <div class="action-controls">
            <button class="btn btn-cancel" on:click={handleLater}>
              {$t("button_later")}
            </button>
            <button class="btn btn-yes" on:click={handleDownload}>
              {$t("button_ok")}
            </button>
          </div>
        {/if}
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
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal-card {
    background: var(--bg-primary, #ffffff);
    border: 1px solid var(--border-color, #cccccc);
    width: 500px;
    max-width: 90vw;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-color, #e0e0e0);
  }

  .modal-header h3 {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
  }

  .close-btn {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 14px;
    color: var(--text-secondary, #666666);
    padding: 2px 6px;
  }

  .close-btn:hover {
    color: var(--text-primary, #000000);
  }

  .modal-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .modal-text {
    margin: 0;
    font-size: 13px;
    line-height: 1.5;
  }

  .repo-link-box {
    padding: 6px 10px;
    background: var(--bg-secondary, #f0f0f0);
    border: 1px solid var(--border-color, #e0e0e0);
    word-break: break-all;
  }

  .repo-link {
    font-size: 12px;
    color: var(--accent, #17bebe);
    text-decoration: underline;
  }

  .repo-link:hover {
    opacity: 0.85;
  }

  .error-text {
    margin: 0;
    font-size: 12px;
    color: #e53935;
  }

  .modal-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #fafafa);
  }

  .action-controls {
    display: flex;
    gap: 8px;
  }

  .status-msg-running {
    font-size: 12px;
    font-style: italic;
    color: var(--text-secondary, #666666);
  }

  .btn {
    padding: 6px 14px;
    font-size: 13px;
    cursor: pointer;
    border: 1px solid var(--border-color, #cccccc);
    background: var(--bg-primary, #ffffff);
    color: var(--text-primary, #000000);
  }

  .btn:hover:not(:disabled) {
    background: var(--bg-hover, #f0f0f0);
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-yes {
    background: var(--accent, #17bebe);
    color: var(--accent-text, #000000);
    border-color: var(--accent, #17bebe);
  }

  .btn-yes:hover:not(:disabled) {
    opacity: 0.9;
  }

  .btn-cancel {
    background: transparent;
  }
</style>
