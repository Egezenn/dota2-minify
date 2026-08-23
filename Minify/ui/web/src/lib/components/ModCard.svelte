<script lang="ts">
  export let name: string;
  export let enabled: boolean;
  export let ontoggle: (value: boolean) => void;

  function handleToggle() {
    ontoggle(!enabled);
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
  <input
    type="checkbox"
    checked={enabled}
    on:change={handleToggle}
    on:click|stopPropagation
  />
</div>

<style>
  .mod-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border: 1px solid #ccc;
    cursor: pointer;
    background: #fff;
    min-height: 40px;
    box-sizing: border-box;
    overflow: hidden;
  }

  .mod-name {
    font-size: 13px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  input[type="checkbox"] {
    cursor: pointer;
  }
</style>
