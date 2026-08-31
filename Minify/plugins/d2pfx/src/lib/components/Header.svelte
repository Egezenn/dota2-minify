<script lang="ts">
  export let categoryName: string = "";
  export let categoryDesc: string = "";
  export let searchQuery: string = "";
  export let onSearchChange: (query: string) => void;
  export let onRefreshData: () => void;

  function handleInput(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target) {
      onSearchChange(target.value);
    }
  }
</script>

<header class="top-bar">
  <div class="cat-info">
    <h3>{categoryName || "Select a category"}</h3>
    {#if categoryDesc}
      <p>{categoryDesc}</p>
    {/if}
  </div>

  <div class="top-actions">
    <input
      type="text"
      placeholder="Search mods..."
      value={searchQuery}
      on:input={handleInput}
    />

    <button class="action-btn" on:click={onRefreshData}>
      Refresh Data
    </button>
  </div>
</header>

<style>
  .top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 38px;
    padding: 0 8px;
    border-bottom: 1px solid #000;
    background: #fff;
    gap: 12px;
    box-sizing: border-box;
  }

  .cat-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .cat-info h3 {
    margin: 0;
    font-size: 15px;
    font-weight: bold;
    text-transform: capitalize;
    line-height: 1;
    display: flex;
    align-items: center;
  }

  .cat-info p {
    font-size: 11px;
    color: #555;
    margin: 0;
    line-height: 1;
    display: flex;
    align-items: center;
  }

  .top-actions {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .top-actions input {
    height: 24px;
    padding: 0 6px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    outline: none;
    font-size: 12px;
    width: 140px;
    box-sizing: border-box;
  }

  .action-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 8px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    cursor: pointer;
    font-weight: bold;
    font-size: 11px;
    line-height: 1;
    box-sizing: border-box;
  }

  .action-btn:hover {
    background: #000;
    color: #fff;
  }
</style>
