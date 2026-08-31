<script lang="ts">
  export let isOpen: boolean = false;
  export let onConfirm: (removeEverything: boolean) => void;
  export let onCancel: () => void;

  let removeEverything: boolean = false;

  function handleConfirm() {
    onConfirm(removeEverything);
  }

  function handleCancel() {
    removeEverything = false;
    onCancel();
  }
</script>

{#if isOpen}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="modal-backdrop" on:click|self={handleCancel}>
    <div class="modal-card">
      <div class="modal-header">
        <h3>Uninstall Mods</h3>
        <button class="close-btn" on:click={handleCancel}>✕</button>
      </div>

      <div class="modal-body">
        <p class="modal-text">
          This will uninstall all the mods related to minify, are you sure?
        </p>

        <label class="checkbox-label">
          <input type="checkbox" bind:checked={removeEverything} />
          <span>Remove everything (Will delete any of the mods you may have manually installed!)</span>
        </label>
      </div>

      <div class="modal-footer">
        <button class="btn btn-cancel" on:click={handleCancel}>Cancel</button>
        <button class="btn btn-yes" on:click={handleConfirm}>Yes</button>
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
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
  }

  .modal-card {
    width: 440px;
    max-width: 90vw;
    background: #fff;
    border: 1px solid #000;
    display: flex;
    flex-direction: column;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid #000;
    background: #fff;
  }

  .modal-header h3 {
    font-size: 14px;
    font-weight: bold;
    margin: 0;
  }

  .close-btn {
    border: none;
    background: transparent;
    font-size: 14px;
    font-weight: bold;
    cursor: pointer;
    line-height: 1;
  }

  .modal-body {
    padding: 16px 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .modal-text {
    font-size: 13px;
    color: #000;
    line-height: 1.4;
  }

  .checkbox-label {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 12px;
    color: #000;
    cursor: pointer;
    user-select: none;
  }

  .checkbox-label input[type="checkbox"] {
    margin-top: 2px;
    cursor: pointer;
  }

  .modal-footer {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;
    padding: 8px 12px;
    border-top: 1px solid #000;
    background: #fff;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 26px;
    padding: 0 16px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-size: 13px;
    font-weight: bold;
    cursor: pointer;
  }

  .btn-yes {
    background: #000;
    color: #fff;
  }
</style>
