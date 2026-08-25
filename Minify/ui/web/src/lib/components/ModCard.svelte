<script lang="ts">
  export let name: string;
  export let enabled: boolean;
  export let ontoggle: (value: boolean) => void;
  export let onDetails: ((name: string) => void) | undefined = undefined;

  function handleToggle() {
    ontoggle(!enabled);
  }

  function handleDetails(e: MouseEvent) {
    e.stopPropagation();
    if (onDetails) {
      onDetails(name);
    }
  }
</script>

<div
  class="mod-card"
  on:click={handleToggle}
  role="button"
  tabindex="0"
  on:keydown={(e) => (e.key === "Enter" || e.key === " ") && handleToggle()}
>
  <span class="mod-name">{name}</span>

  <div class="mod-actions">
    {#if onDetails}
      <button class="details-btn" type="button" on:click={handleDetails}>
        Details
      </button>
    {/if}
    <input
      type="checkbox"
      checked={enabled}
      on:change={handleToggle}
      on:click|stopPropagation
    />
  </div>
</div>

<style>
  .mod-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border: 1px solid #000;
    cursor: pointer;
    background: #fff;
    min-height: 40px;
    gap: 8px;
  }

  .mod-name {
    font-size: 13px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .mod-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .details-btn {
    padding: 2px 6px;
    font-size: 11px;
    color: #000;
    background: #fff;
    border: 1px solid #000;
    cursor: pointer;
  }

  input[type="checkbox"] {
    cursor: pointer;
  }
</style>
