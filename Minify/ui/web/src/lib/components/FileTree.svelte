<script lang="ts">
  import { t } from "../i18n";

  export let node: any;
  export let depth: number = 0;
  export let isRoot: boolean = true;

  let expanded: boolean = true;

  function toggle() {
    expanded = !expanded;
  }

  function formatSize(bytes?: number): string {
    if (bytes === undefined || bytes === null || bytes === 0) return "";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
</script>

{#if isRoot}
  <div class="file-tree-root">
    {#if node && node.children && node.children.length > 0}
      {#each node.children as child (child.path || child.name)}
        <svelte:self node={child} depth={0} isRoot={false} />
      {/each}
    {:else}
      <div class="tree-empty">{$t("label_empty_directory")}</div>
    {/if}
  </div>
{:else if node.type === "directory"}
  <div class="tree-dir-row" style="padding-left: {depth * 18}px;">
    <button class="tree-toggle-btn" type="button" on:click={toggle}>
      <span class="tree-chevron {expanded ? 'expanded' : ''}">▶</span>
      <span class="tree-icon">{expanded ? "📂" : "📁"}</span>
      <span class="tree-name">{node.name}</span>
      {#if node.children}
        <span class="tree-badge">({node.children.length})</span>
      {/if}
    </button>
  </div>
  {#if expanded && node.children}
    {#each node.children as child (child.path || child.name)}
      <svelte:self node={child} depth={depth + 1} isRoot={false} />
    {/each}
  {/if}
{:else}
  <div class="tree-file-row" style="padding-left: {depth * 18 + 14}px;">
    <span class="tree-icon">📄</span>
    <span class="tree-name">{node.name}</span>
    {#if node.size !== undefined && node.size > 0}
      <span class="file-size">{formatSize(node.size)}</span>
    {/if}
  </div>
{/if}

<style>
  .file-tree-root {
    padding: 8px 12px;
    font-family: var(--font-mono, monospace);
    font-size: 12px;
    color: var(--text-primary, #000);
    overflow-x: auto;
  }

  .tree-empty {
    color: var(--text-muted, #888);
    font-style: italic;
    padding: 8px 0;
  }

  .tree-dir-row,
  .tree-file-row {
    display: flex;
    align-items: center;
    height: 24px;
    line-height: 24px;
    user-select: none;
    white-space: nowrap;
  }

  .tree-dir-row:hover,
  .tree-file-row:hover {
    background: var(--btn-hover-bg, rgba(0, 0, 0, 0.04));
  }

  .tree-toggle-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    background: transparent;
    border: none;
    color: inherit;
    font-family: inherit;
    font-size: inherit;
    cursor: pointer;
    padding: 0;
    margin: 0;
    outline: none;
  }

  .tree-toggle-btn:hover .tree-name {
    color: var(--accent, #17bebe);
  }

  .tree-chevron {
    display: inline-block;
    width: 10px;
    font-size: 8px;
    color: var(--text-muted, #888);
    transition: transform 0.15s ease;
  }

  .tree-chevron.expanded {
    transform: rotate(90deg);
  }

  .tree-icon {
    font-size: 13px;
    display: inline-flex;
    align-items: center;
  }

  .tree-name {
    color: var(--text-primary, #000);
  }

  .tree-badge {
    color: var(--text-muted, #888);
    font-size: 11px;
    margin-left: 4px;
  }

  .file-size {
    color: var(--text-muted, #888);
    font-size: 11px;
    margin-left: 8px;
  }
</style>
