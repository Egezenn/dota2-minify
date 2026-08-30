<script lang="ts">
  export interface DownloadItem {
    id: string;
    name: string;
    downloaded_bytes: number;
    total_bytes: number;
    status: "downloading" | "finished" | "error";
    error?: string;
  }

  export let downloads: DownloadItem[] = [];
  export let onDismiss: (id: string) => void = () => {};

  function formatMB(bytes: number): string {
    if (!bytes || bytes < 0) return "0.00 MB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  }

  function getPercent(item: DownloadItem): number {
    if (!item.total_bytes || item.total_bytes <= 0) return 0;
    return Math.min(100, Math.round((item.downloaded_bytes / item.total_bytes) * 100));
  }
</script>

{#if downloads.length > 0}
  <div class="download-container">
    {#each downloads as item (item.id)}
      <div class="download-card {item.status}">
        <div class="download-header">
          <span class="download-title">{item.name}</span>
          <button class="close-btn" on:click={() => onDismiss(item.id)} title="Dismiss">×</button>
        </div>

        {#if item.status === "downloading"}
          <div class="download-stats">
            {#if item.total_bytes > 0}
              {formatMB(item.downloaded_bytes)} / {formatMB(item.total_bytes)} ({getPercent(item)}%)
            {:else}
              {formatMB(item.downloaded_bytes)}
            {/if}
          </div>
          {#if item.total_bytes > 0}
            <div class="progress-bar-bg">
              <div class="progress-bar-fill" style="width: {getPercent(item)}%"></div>
            </div>
          {/if}
        {:else if item.status === "finished"}
          <div class="download-status-text finished">
            ✓ Download Complete ({formatMB(item.downloaded_bytes)})
          </div>
        {:else if item.status === "error"}
          <div class="download-status-text error">
            Failed: {item.error || "Unknown error"}
          </div>
        {/if}
      </div>
    {/each}
  </div>
{/if}

<style>
  *,
  *::before,
  *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    border-radius: 0 !important;
    box-shadow: none !important;
    transition: none !important;
    animation: none !important;
  }

  .download-container {
    position: fixed;
    bottom: 12px;
    right: 12px;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 300px;
    max-width: calc(100vw - 24px);
    pointer-events: auto;
  }

  .download-card {
    background: #fff;
    color: #000;
    border: 1px solid #000;
    padding: 8px 10px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }

  .download-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
    font-size: 12px;
    margin-bottom: 4px;
  }

  .download-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 250px;
  }

  .close-btn {
    background: transparent;
    border: none;
    cursor: pointer;
    font-weight: bold;
    font-size: 14px;
    color: #000;
    line-height: 1;
    padding: 0 2px;
  }

  .close-btn:hover {
    color: #ff0000;
  }

  .download-stats {
    font-size: 11px;
    font-family: monospace;
    margin-bottom: 6px;
    color: #333;
  }

  .progress-bar-bg {
    height: 6px;
    background: #eee;
    border: 1px solid #000;
    width: 100%;
    overflow: hidden;
  }

  .progress-bar-fill {
    height: 100%;
    background: #000;
  }

  .download-status-text {
    font-size: 11px;
    font-weight: bold;
    margin-top: 2px;
  }

  .download-status-text.finished {
    color: #000;
  }

  .download-status-text.error {
    color: #cc0000;
  }
</style>
