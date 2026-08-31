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

  function cleanAnsi(text: string): string {
    if (!text) return "";
    return text.replace(/\033\[[0-9;]*m/g, "").replace(/\x1b\[[0-9;]*m/g, "");
  }
</script>

<div class="terminal-container">
  <div class="terminal-toolbar">
    <div class="toolbar-title">
      <h3>Terminal</h3>
    </div>

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
        <div class="log-row {log.type || 'info'}">{cleanAnsi(log.text)}</div>
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
    height: 38px;
    padding: 0 8px;
    border-bottom: 1px solid #000;
    font-size: 13px;
    box-sizing: border-box;
  }

  .toolbar-title {
    display: flex;
    align-items: center;
  }

  .toolbar-title h3 {
    margin: 0;
    font-size: 15px;
    font-weight: bold;
    line-height: 1;
    display: flex;
    align-items: center;
  }

  .toolbar-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .toolbar-controls label {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    line-height: 1;
    cursor: pointer;
  }

  .toolbar-controls button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 8px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    line-height: 1;
    cursor: pointer;
    box-sizing: border-box;
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
    user-select: text;
    cursor: text;
  }

  .log-row {
    white-space: pre-wrap;
    word-break: break-all;
    user-select: text;
    cursor: text;
    color: #000;
  }

  .log-row.error {
    color: #cc0000;
    font-weight: bold;
  }

  .log-row.warning {
    color: #d97706;
  }

  .log-row.success {
    color: #2e7d32;
    font-weight: bold;
  }

  hr {
    border: none;
    border-top: 1px solid #000;
    margin: 4px 0;
  }
</style>
