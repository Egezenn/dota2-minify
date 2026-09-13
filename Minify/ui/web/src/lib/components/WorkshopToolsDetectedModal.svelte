<script lang="ts">
  import { t } from "../i18n";

  export let isOpen: boolean = false;
  export let onExtract: () => void;
  export let onSkip: () => void;
  export let onCancel: () => void;

  function handleExtract() {
    onExtract();
  }

  function handleSkip() {
    onSkip();
  }

  function handleClose() {
    onCancel();
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-backdrop" on:click|self={handleClose}>
    <div class="modal-card">
      <div class="modal-header">
        <h3>{$t("title_extract_workshop_tools")}</h3>
        <button class="close-btn" on:click={handleClose}>✕</button>
      </div>

      <div class="modal-body">
        <p class="modal-text">
          {$t("modal_workshop_tools_detected")}
        </p>
        <p class="modal-subtext">
          {$t("modal_workshop_tools_prompt")}
        </p>
      </div>

      <div class="modal-footer">
        <button class="btn btn-cancel" on:click={handleClose}>{$t("button_cancel")}</button>
        <button class="btn btn-skip" on:click={handleSkip}>{$t("button_skip")}</button>
        <button class="btn btn-extract" on:click={handleExtract}>{$t("button_extract")}</button>
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
    background: var(--bg-primary, #ffffff);
    border: 1px solid var(--border-color, #e0e0e0);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    width: 480px;
    max-width: 90vw;
    display: flex;
    flex-direction: column;
    color: var(--text-primary, #111111);
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
    font-size: 15px;
    font-weight: 600;
  }

  .close-btn {
    background: transparent;
    border: none;
    font-size: 14px;
    cursor: pointer;
    color: var(--text-secondary, #666666);
  }

  .close-btn:hover {
    color: var(--text-primary, #111111);
  }

  .modal-body {
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .modal-text {
    margin: 0;
    font-size: 13px;
    line-height: 1.4;
  }

  .modal-subtext {
    margin: 0;
    font-size: 12px;
    color: var(--text-secondary, #666666);
    line-height: 1.4;
  }

  .modal-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding: 12px 16px;
    gap: 8px;
    border-top: 1px solid var(--border-color, #e0e0e0);
    background: var(--bg-secondary, #f8f9fa);
  }

  .btn {
    padding: 6px 14px;
    font-size: 12px;
    cursor: pointer;
    border: 1px solid var(--border-color, #cccccc);
    background: var(--bg-primary, #ffffff);
    color: var(--text-primary, #111111);
  }

  .btn:hover {
    background: var(--bg-hover, #f0f0f0);
  }

  .btn-cancel {
    margin-right: auto;
  }

  .btn-extract {
    background: var(--accent, #17bebe);
    color: var(--accent-text, #000000);
    border-color: var(--accent, #17bebe);
  }

  .btn-extract:hover {
    opacity: 0.9;
  }
</style>
