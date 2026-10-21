<script lang="ts">
  import { t } from "../i18n";

  export let isOpen = false;
  export let entries: string[] = [];
  export let onImport: () => void;
  export let onDiscard: () => void;
</script>

{#if isOpen}
  <div class="modal-backdrop">
    <div class="modal-card" role="dialog" aria-modal="true">
      <header class="modal-header"><h3>{$t("title_import_legacy_mods")}</h3></header>
      <div class="modal-body">
        <p>{$t("modal_import_legacy_mods")}</p>
        <ul>{#each entries as entry}<li>{entry}</li>{/each}</ul>
      </div>
      <footer class="modal-footer">
        <button class="btn btn-discard" on:click={onDiscard}>{$t("button_discard")}</button>
        <button class="btn btn-import" on:click={onImport}>{$t("button_import")}</button>
      </footer>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop { position: fixed; inset: 0; z-index: 10000; display: flex; align-items: center; justify-content: center; background: var(--modal-backdrop, rgba(0, 0, 0, 0.5)); }
  .modal-card { width: 480px; max-width: 90vw; background: var(--bg-primary, #fff); color: var(--text-primary, #111); border: 1px solid var(--border-color, #e0e0e0); }
  .modal-header, .modal-body, .modal-footer { padding: 12px 16px; }
  .modal-header { border-bottom: 1px solid var(--border-color, #e0e0e0); }
  .modal-header h3 { margin: 0; font-size: 15px; }
  .modal-body { font-size: 13px; }
  ul { max-height: 220px; overflow: auto; padding-left: 20px; }
  .modal-footer { display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid var(--border-color, #e0e0e0); background: var(--bg-secondary, #f8f9fa); }
  .btn { padding: 6px 14px; cursor: pointer; }
  .btn-import { background: var(--accent, #17bebe); color: var(--accent-text, #000); }
</style>
