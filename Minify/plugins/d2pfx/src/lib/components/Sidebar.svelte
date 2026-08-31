<script lang="ts">
  import type { Category } from "../types";

  export let categories: Category[] = [];
  export let selectedCategory: string = "";
  export let isLoadingCategories: boolean = false;
  export let onSelectCategory: (cat: Category) => void;

  let searchQuery = "";

  $: filteredCategories = categories.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );
</script>

<aside class="sidebar">
  <div class="sidebar-search">
    <input
      type="text"
      placeholder="Search categories..."
      bind:value={searchQuery}
    />
  </div>
  <div class="category-list">
    {#if isLoadingCategories}
      <div class="loading-item">Loading categories...</div>
    {:else}
      {#each filteredCategories as cat}
        <button
          class="category-item {selectedCategory === cat.id ? 'active' : ''}"
          on:click={() => onSelectCategory(cat)}
        >
          {cat.name}
        </button>
      {/each}
    {/if}
  </div>
</aside>

<style>
  .sidebar {
    width: 180px;
    border-right: 1px solid #000;
    display: flex;
    flex-direction: column;
    background: #fff;
    flex-shrink: 0;
  }

  .sidebar-search {
    height: 38px;
    padding: 0 8px;
    border-bottom: 1px solid #000;
    display: flex;
    align-items: center;
    box-sizing: border-box;
  }

  .sidebar-search input {
    width: 100%;
    height: 24px;
    padding: 0 6px;
    border: 1px solid #000;
    background: #fff;
    color: #000;
    font-size: 12px;
    outline: none;
    box-sizing: border-box;
  }

  .category-list {
    flex: 1;
    overflow-y: auto;
  }

  .loading-item {
    padding: 8px;
    font-size: 11px;
    color: #666;
  }

  .category-item {
    width: 100%;
    padding: 6px 8px;
    text-align: left;
    border: none;
    border-bottom: 1px solid #eee;
    background: #fff;
    color: #000;
    cursor: pointer;
    font-size: 12px;
  }

  .category-item:hover,
  .category-item.active {
    background: #000;
    color: #fff;
  }
</style>
