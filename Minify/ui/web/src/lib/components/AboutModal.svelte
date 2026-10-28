<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { t } from "../i18n";

  export let isOpen: boolean = false;
  export let readme: string = "";
  export let licenseText: string = "";
  export let onClose: () => void;

  let activeTab: "readme" | "license" = "readme";

  function handleKeydown(e: KeyboardEvent) {
    if (!isOpen) return;
    if (e.key === "Escape") {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeydown);
  });

  function handleClose() {
    onClose();
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-backdrop" on:click|self={handleClose}>
    <div class="modal-card">
      <div class="modal-header">
        <h3>About</h3>
        <button class="close-btn" on:click={handleClose}>✕</button>
      </div>

      <div class="modal-tabs">
        <button class="tab-btn" class:active={activeTab === "readme"} on:click={() => (activeTab = "readme")}>
          README
        </button>
        <button class="tab-btn" class:active={activeTab === "license"} on:click={() => (activeTab = "license")}>
          LICENSE
        </button>
      </div>

      <div class="modal-body">
        {#if activeTab === "readme"}
          <pre class="content">{readme || "No README found."}</pre>
        {:else}
          <pre class="content">{licenseText || "No LICENSE found."}</pre>
        {/if}
      </div>

      <div class="modal-footer">
        <button class="btn btn-cancel" on:click={handleClose}>{$t("button_close")}</button>
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
    width: 800px;
    max-width: 90vw;
    max-height: 90vh;
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

  .modal-header h3 {
    font-size: 14px;
    font-weight: bold;
    margin: 0;
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

  .modal-tabs {
    display: flex;
    gap: 4px;
    padding: 8px 12px 0 12px;
    border-bottom: 1px solid var(--border-color, #000);
  }

  .tab-btn {
    border: 1px solid var(--btn-border, #000);
    border-bottom: none;
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    padding: 4px 12px;
    font-size: 12px;
    cursor: pointer;
    font-weight: bold;
  }

  .tab-btn.active {
    background: var(--accent, #17bebe);
    color: #fff;
    border-color: var(--accent, #17bebe);
  }

  .modal-body {
    flex: 1;
    overflow: auto;
    padding: 12px;
    min-height: 300px;
    max-height: 60vh;
  }

  .content {
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
    color: var(--text-primary, #000);
    line-height: 1.4;
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 8px 12px;
    border-top: 1px solid var(--border-color, #000);
    background: var(--modal-bg, #fff);
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 12px;
    border: 1px solid var(--btn-border, #000);
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    font-size: 12px;
    font-family: inherit;
    font-weight: bold;
    line-height: 1;
    cursor: pointer;
    box-sizing: border-box;
  }

  .btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .btn-cancel {
    min-width: 70px;
  }
</style>
