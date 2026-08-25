<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { marked } from "marked";
  import markedAlert from "marked-alert";

  export let modName: string | null = null;
  export let onClose: () => void;

  let loading = true;
  let details: {
    name: string;
    notes: string | null;
    preview: string | null;
    has_notes: boolean;
    has_preview: boolean;
  } | null = null;

  marked.setOptions({
    gfm: true,
    breaks: true,
  });

  marked.use(markedAlert());

  $: if (modName) {
    fetchDetails(modName);
  }

  async function fetchDetails(name: string) {
    loading = true;
    details = null;
    try {
      if (window.pywebview?.api?.get_mod_details) {
        details = await window.pywebview.api.get_mod_details(name);
      }
    } catch (err) {
      console.error("Failed to load mod details:", err);
    } finally {
      loading = false;
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      onClose();
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeyDown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeyDown);
  });

  function formatNotes(markdown: string | null): string {
    if (!markdown) return "";
    return marked.parse(markdown) as string;
  }
</script>

{#if modName}
  <div
    class="modal-backdrop"
    on:click={onClose}
    role="button"
    tabindex="-1"
    on:keydown={(e) => e.key === "Escape" && onClose()}
  >
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <div
      class="modal-card"
      on:click|stopPropagation
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
    >
      <header class="modal-header">
        <h2 id="modal-title">{modName}</h2>
        <button
          class="close-btn"
          type="button"
          on:click={onClose}
          aria-label="Close modal"
        >
          &times;
        </button>
      </header>

      <div class="modal-body">
        {#if loading}
          <div class="loading-state">Loading...</div>
        {:else if details}
          {#if details.has_preview && details.preview}
            <div class="image-wrapper">
              <img src={details.preview} alt={`Preview for ${modName}`} />
            </div>
          {/if}

          {#if details.has_notes && details.notes}
            <div class="notes-content">
              {@html formatNotes(details.notes)}
            </div>
          {:else if !details.has_preview}
            <div class="empty-state">No notes or preview available.</div>
          {/if}
        {/if}
      </div>

      <footer class="modal-footer">
        <button class="btn-close" type="button" on:click={onClose}>
          Close
        </button>
      </footer>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-card {
    background: #fff;
    width: 90%;
    max-width: 600px;
    max-height: 85vh;
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
  }

  .modal-header h2 {
    font-size: 15px;
    margin: 0;
  }

  .close-btn {
    background: #fff;
    color: #000;
    border: 1px solid #000;
    padding: 2px 8px;
    cursor: pointer;
  }

  .modal-body {
    padding: 12px;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .loading-state,
  .empty-state {
    padding: 16px;
    text-align: center;
    font-size: 13px;
  }

  .image-wrapper img {
    max-width: 100%;
    max-height: 300px;
    display: block;
    margin: 0 auto;
  }

  .notes-content {
    border: 1px solid #000;
    padding: 8px 12px;
    font-size: 13px;
    line-height: 1.4;
  }

  .notes-content :global(.markdown-alert) {
    border: 1px solid #000;
    border-left: 4px solid #000;
    padding: 6px 10px;
    margin: 6px 0;
    background: #fff;
    color: #000;
  }

  .notes-content :global(.markdown-alert-title) {
    font-weight: bold;
    font-size: 12px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .notes-content :global(p) {
    margin-bottom: 0.75em;
  }

  .notes-content :global(p:last-child) {
    margin-bottom: 0;
  }

  .notes-content :global(h1),
  .notes-content :global(h2),
  .notes-content :global(h3) {
    font-size: 14px;
    font-weight: bold;
    margin-top: 12px;
    margin-bottom: 6px;
  }

  .notes-content :global(ul),
  .notes-content :global(ol) {
    padding-left: 20px;
    margin-top: 4px;
    margin-bottom: 8px;
  }

  .notes-content :global(pre) {
    border: 1px solid #000;
    padding: 8px 12px;
    margin: 6px 0;
    background: #f8f9fa;
    overflow-x: auto;
  }

  .notes-content :global(pre code) {
    border: none;
    padding: 0;
    background: transparent;
    white-space: pre;
  }

  .notes-content :global(code) {
    border: 1px solid #000;
    padding: 1px 4px;
    font-family: monospace;
    font-size: 12px;
  }

  .modal-footer {
    padding: 8px 12px;
    border-top: 1px solid #000;
    display: flex;
    justify-content: flex-end;
  }

  .btn-close {
    background: #fff;
    color: #000;
    border: 1px solid #000;
    padding: 4px 12px;
    cursor: pointer;
  }
</style>
