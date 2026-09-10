<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import type { UpdateInfo, DownloadItem } from "../types";

  export let isOpen: boolean = false;
  export let updateInfo: UpdateInfo | null = null;
  export let downloads: DownloadItem[] = [];
  export let onIgnore: (version: string) => void;
  export let onClose: () => void;

  let isDownloading = false;
  let downloadStatus: "idle" | "downloading" | "finished" | "error" = "idle";
  let downloadedBytes = 0;
  let totalBytes = 0;
  let errorMessage = "";

  $: updateDownload = downloads.find(
    (d) =>
      d.name.toLowerCase().includes("setup") ||
      d.name.toLowerCase().includes("minify") ||
      d.id.toLowerCase().includes("setup") ||
      d.id === "app-update",
  );

  $: if (updateDownload) {
    isDownloading = true;
    downloadedBytes = updateDownload.downloaded_bytes;
    totalBytes = updateDownload.total_bytes;
    if (updateDownload.status === "finished") {
      downloadStatus = "finished";
    } else if (updateDownload.status === "error") {
      downloadStatus = "error";
      errorMessage = updateDownload.error || "Download failed";
    }
  }

  function formatMB(bytes: number): string {
    if (!bytes || bytes < 0) return "0.00 MB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  }

  function getPercent(downloaded: number, total: number): number {
    if (!total || total <= 0) return 0;
    return Math.min(100, Math.round((downloaded / total) * 100));
  }

  function getFileName(url: string): string | null {
    try {
      const parsed = new URL(url);
      const parts = parsed.pathname.split("/");
      return parts[parts.length - 1] || null;
    } catch {
      return null;
    }
  }

  async function handleStartDownload() {
    if (!updateInfo) return;
    const url = updateInfo.downloadUrl || updateInfo.releaseUrl;
    if (!url) return;

    isDownloading = true;
    downloadStatus = "downloading";
    downloadedBytes = 0;
    totalBytes = 0;
    errorMessage = "";

    const api = window.pywebview?.api;
    if (api?.perform_update) {
      try {
        const handled = await api.perform_update(url);
        if (!handled) {
          downloadStatus = "idle";
          isDownloading = false;
          onClose();
          return;
        }
      } catch (err: any) {
        console.error("perform_update failed:", err);
        downloadStatus = "error";
        errorMessage = err?.message || "Failed to start update";
      }
    } else {
      window.open("https://egezenn.github.io/dota2-minify", "_blank");
      downloadStatus = "idle";
      isDownloading = false;
      onClose();
    }
  }

  function handleIgnore() {
    if (!updateInfo) return;
    onIgnore(updateInfo.version);
  }

  function handleCloseModal() {
    onClose();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (!isOpen) return;
    if (e.key === "Escape" && !isDownloading) {
      handleCloseModal();
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeydown);
  });
</script>

{#if isOpen && updateInfo}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div
    class="modal-backdrop"
    on:click|self={() => {
      if (!isDownloading) handleCloseModal();
    }}
  >
    <div class="modal-card">
      <div class="modal-header">
        <div class="header-title-group">
          <h3>Update Available</h3>
          <span class="badge">v{updateInfo.version}</span>
        </div>
        {#if !isDownloading}
          <button class="close-btn" on:click={handleCloseModal} title="Close"
            >✕</button
          >
        {/if}
      </div>

      <div class="modal-body">
        <p class="modal-text">
          A new version of Dota 2 Minify is available to download.
        </p>

        <div class="version-box">
          <div class="version-col">
            <span class="version-label">Current:</span>
            <span class="version-value">v{updateInfo.currentVersion}</span>
          </div>
          <span class="version-arrow">➔</span>
          <div class="version-col">
            <span class="version-label">New:</span>
            <span class="version-value new-version">v{updateInfo.version}</span>
          </div>
        </div>

        {#if isDownloading}
          <div class="download-section">
            <div class="download-info">
              <span class="download-name"
                >{getFileName(updateInfo.downloadUrl || "") || updateDownload?.name || ""}</span
              >
              <span class="download-numbers">
                {#if totalBytes > 0}
                  {formatMB(downloadedBytes)} / {formatMB(totalBytes)} ({getPercent(
                    downloadedBytes,
                    totalBytes,
                  )}%)
                {:else}
                  {formatMB(downloadedBytes)}
                {/if}
              </span>
            </div>

            <div class="progress-bar-bg">
              <div
                class="progress-bar-fill"
                style="width: {getPercent(downloadedBytes, totalBytes)}%"
              ></div>
            </div>

            {#if downloadStatus === "finished"}
              <div class="status-msg finished">
                ✓ Download complete! Launching installer and closing Minify...
              </div>
            {:else if downloadStatus === "error"}
              <div class="status-msg error">
                ✕ {errorMessage}
              </div>
            {/if}
          </div>
        {:else if updateInfo.body}
          <div class="changelog-container">
            <span class="changelog-label">Release Notes:</span>
            <div class="changelog-box">
              {updateInfo.body}
            </div>
          </div>
        {/if}
      </div>

      <div class="modal-footer">
        {#if !isDownloading}
          <button class="btn btn-cancel" on:click={handleIgnore}>
            Ignore This Version
          </button>

          <div class="action-controls">
            <button class="btn btn-cancel" on:click={handleCloseModal}
              >Later</button
            >
            <button class="btn btn-yes" on:click={handleStartDownload}
              >Update Now</button
            >
          </div>
        {:else if downloadStatus === "downloading"}
          <div class="status-msg-running">Downloading...</div>
          <div class="action-controls">
            <button class="btn btn-yes" disabled>Downloading...</button>
          </div>
        {:else if downloadStatus === "finished"}
          <div class="status-msg finished">Launching installer...</div>
          <div class="action-controls">
            <button class="btn btn-yes" disabled>Closing...</button>
          </div>
        {:else if downloadStatus === "error"}
          <button class="btn btn-cancel" on:click={handleCloseModal}
            >Close</button
          >
          <div class="action-controls">
            <button class="btn btn-yes" on:click={handleStartDownload}
              >Retry</button
            >
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
    background: var(--modal-backdrop, rgba(0, 0, 0, 0.5));
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10001;
  }

  .modal-card {
    width: 480px;
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
    padding: 2px 6px;
    background: var(--accent, #17bebe);
    color: var(--accent-text, #000);
    font-weight: bold;
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
    gap: 14px;
    overflow-y: auto;
  }

  .modal-text {
    font-size: 13px;
    color: var(--text-primary, #000);
    line-height: 1.4;
  }

  .version-box {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 10px 14px;
    background: var(--bg-secondary, #f8f9fa);
    border: 1px solid var(--border-color, #eee);
  }

  .version-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }

  .version-label {
    font-size: 11px;
    text-transform: uppercase;
    color: var(--text-secondary, #666);
  }

  .version-value {
    font-size: 13px;
    font-weight: bold;
    font-family: monospace;
  }

  .new-version {
    color: var(--accent, #17bebe);
  }

  .version-arrow {
    font-size: 14px;
    color: var(--text-secondary, #666);
  }

  .changelog-container {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .changelog-label {
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    color: var(--text-secondary, #666);
  }

  .changelog-box {
    max-height: 180px;
    overflow-y: auto;
    padding: 8px 10px;
    font-size: 12px;
    line-height: 1.4;
    white-space: pre-wrap;
    word-break: break-word;
    background: var(--bg-primary, #fff);
    border: 1px solid var(--border-color, #eee);
    color: var(--text-primary, #000);
  }

  .download-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    background: var(--bg-secondary, #f8f9fa);
    border: 1px solid var(--border-color, #eee);
  }

  .download-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    font-weight: bold;
  }

  .download-numbers {
    font-family: monospace;
    font-size: 11px;
    color: var(--text-secondary, #666);
  }

  .progress-bar-bg {
    height: 8px;
    background: var(--bg-primary, #fff);
    border: 1px solid var(--border-color, #000);
    width: 100%;
    overflow: hidden;
  }

  .progress-bar-fill {
    height: 100%;
    background: var(--accent, #17bebe);
    transition: width 0.1s linear;
  }

  .status-msg {
    font-size: 12px;
    font-weight: bold;
    margin-top: 2px;
  }

  .status-msg-running {
    font-size: 11px;
    color: var(--text-secondary, #666);
    font-style: italic;
  }

  .status-msg.finished {
    color: var(--accent, #17bebe);
  }

  .status-msg.error {
    color: var(--log-error, #cc0000);
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

  .action-controls {
    display: flex;
    align-items: center;
    gap: 8px;
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
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-cancel:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

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
