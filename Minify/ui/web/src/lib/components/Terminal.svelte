<script lang="ts">
  import { tick } from "svelte";

  export let logs: Array<{ text: string; type: string; timestamp?: string }> =
    [];
  export let autoScroll: boolean = true;
  export let onClear: () => void;

  let terminalElement: HTMLElement | null = null;

  $: if (autoScroll && logs.length) {
    scrollToBottom();
  }

  async function scrollToBottom() {
    await tick();
    if (terminalElement) {
      terminalElement.scrollTop = terminalElement.scrollHeight;
    }
  }
</script>

<div class="terminal-container">
  <div class="terminal-toolbar">
    <span>Terminal</span>

    <div class="toolbar-controls">
      <label>
        <input type="checkbox" bind:checked={autoScroll} />
        Auto-scroll
      </label>
      <button on:click={onClear}> Clear </button>
    </div>
  </div>

  <div class="terminal-body" bind:this={terminalElement}>
    {#each logs as log}
      {#if log.type === "separator"}
        <hr />
      {:else}
        <div class="log-row">{log.text}</div>
      {/if}
    {/each}
  </div>
</div>

<style>
  .terminal-container {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .terminal-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 8px;
    border-bottom: 1px solid #000;
    font-size: 13px;
  }

  .toolbar-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .toolbar-controls button {
    padding: 2px 8px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    cursor: pointer;
  }

  .terminal-body {
    flex: 1;
    padding: 8px;
    font-family: monospace;
    font-size: 12px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .log-row {
    white-space: pre-wrap;
    word-break: break-all;
  }

  hr {
    border: none;
    border-top: 1px solid #000;
    margin: 4px 0;
  }
</style>
