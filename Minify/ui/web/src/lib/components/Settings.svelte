<script lang="ts">
  import { onMount } from "svelte";

  export let active: boolean = false;
  export let onSettingChange: (key: string, value: any) => void;

  interface SettingItem {
    key: string;
    text: string;
    type: string;
    default?: any;
    mod?: string | null;
    force?: boolean;
    items?: string[];
    var_type?: "int" | "float";
    step?: number;
    min?: number;
    max?: number;
  }

  let schema: SettingItem[] = [];
  let values: Record<string, any> = {};

  let newListItemInputs: Record<string, string> = {};

  async function loadSettings() {
    try {
      if (window.pywebview?.api?.get_settings) {
        const data = await window.pywebview.api.get_settings();
        if (data.schema && Array.isArray(data.schema)) {
          schema = data.schema;
        }
        if (data.values) {
          values = { ...values, ...data.values };
        }
      }
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  }

  onMount(() => {
    loadSettings();
    if (typeof window !== "undefined" && !window.pywebview?.api) {
      window.addEventListener("pywebviewready", loadSettings, { once: true });
    }
  });

  $: if (active) {
    loadSettings();
  }

  async function updateSetting(item: SettingItem, newValue: any) {
    values[item.key] = newValue;
    values = { ...values };

    if (item.mod) {
      if (window.pywebview?.api?.set_setting) {
        await window.pywebview.api.set_setting(item.key, newValue, item.mod);
      }
    } else {
      onSettingChange(item.key, newValue);
    }
  }

  async function runModFunction(item: SettingItem) {
    if (item.mod && window.pywebview?.api?.run_mod_function) {
      await window.pywebview.api.run_mod_function(item.mod, item.key);
    }
  }

  function getItemValue(item: SettingItem): any {
    return values[item.key] ?? item.default;
  }

  function getListValue(item: SettingItem): string[] {
    const val = getItemValue(item);
    return Array.isArray(val) ? [...val] : [];
  }

  function updateListEntry(item: SettingItem, index: number, val: string) {
    const list = getListValue(item);
    list[index] = val;
    updateSetting(item, list);
  }

  function removeListEntry(item: SettingItem, index: number) {
    const list = getListValue(item);
    list.splice(index, 1);
    updateSetting(item, list);
  }

  function addListEntry(item: SettingItem) {
    const inputVal = (newListItemInputs[item.key] || "").trim();
    if (!inputVal) return;
    const list = getListValue(item);
    list.push(inputVal);
    newListItemInputs[item.key] = "";
    newListItemInputs = { ...newListItemInputs };
    updateSetting(item, list);
  }

  function getHex6(colorStr: any): string {
    if (typeof colorStr !== "string") return "#000000";
    if (colorStr.startsWith("#") && colorStr.length >= 7) {
      return colorStr.substring(0, 7);
    }
    return "#000000";
  }

  async function resetSection(sectionTitle: string, items: SettingItem[]) {
    try {
      const isNative =
        sectionTitle === "Application Settings" || !items[0]?.mod;
      if (isNative) {
        if (window.pywebview?.api?.reset_native_settings) {
          await window.pywebview.api.reset_native_settings();
        }
      } else {
        const modName = items[0]?.mod;
        if (modName && window.pywebview?.api?.reset_mod_settings) {
          await window.pywebview.api.reset_mod_settings(modName);
        }
      }
      await loadSettings();
    } catch (err) {
      console.error(`Failed to reset section ${sectionTitle}:`, err);
    }
  }

  $: sections = (() => {
    const map = new Map<string, SettingItem[]>();
    for (const item of schema) {
      const secName = item.mod ? item.mod : "Application Settings";
      if (!map.has(secName)) {
        map.set(secName, []);
      }
      map.get(secName)!.push(item);
    }
    return Array.from(map.entries());
  })();
</script>

<div class="settings-container">
  <div class="settings-toolbar">
    <div class="toolbar-title">
      <h3>Settings</h3>
    </div>
    <div class="toolbar-controls">
      <button class="btn-refresh" on:click={loadSettings}>Refresh</button>
    </div>
  </div>

  <div class="settings-body">
    {#each sections as [sectionTitle, items]}
      <div class="settings-section">
        <div class="section-header">
          <h4 class="section-title">{sectionTitle}</h4>
          <button
            class="btn-reset"
            on:click={() => resetSection(sectionTitle, items)}
          >
            Reset
          </button>
        </div>
        <div class="section-content">
          {#each items as item (item.key)}
            {#if item.type === "checkbox"}
              <label class="setting-item-checkbox">
                <input
                  type="checkbox"
                  checked={Boolean(getItemValue(item))}
                  on:change={(e) =>
                    updateSetting(item, e.currentTarget.checked)}
                />
                <span class="setting-text">{item.text}</span>
              </label>
            {:else if item.type === "inputbox"}
              <div class="setting-item-row">
                <span class="setting-label">{item.text}</span>
                <input
                  type="text"
                  class="setting-input"
                  value={getItemValue(item) ?? ""}
                  on:change={(e) => updateSetting(item, e.currentTarget.value)}
                />
              </div>
            {:else if item.type === "combo"}
              <div class="setting-item-row">
                <span class="setting-label">{item.text}</span>
                <select
                  class="setting-select"
                  value={getItemValue(item) ?? ""}
                  on:change={(e) => updateSetting(item, e.currentTarget.value)}
                >
                  {#each item.items || [] as option}
                    <option value={option}>{option}</option>
                  {/each}
                </select>
              </div>
            {:else if item.type === "number"}
              <div class="setting-item-row">
                <span class="setting-label">{item.text}</span>
                <input
                  type="number"
                  class="setting-input setting-number"
                  step={item.step ?? (item.var_type === "float" ? 0.1 : 1)}
                  min={item.min ?? undefined}
                  max={item.max ?? undefined}
                  value={getItemValue(item) ?? 0}
                  on:change={(e) => {
                    const val =
                      item.var_type === "float"
                        ? parseFloat(e.currentTarget.value)
                        : parseInt(e.currentTarget.value, 10);
                    updateSetting(item, isNaN(val) ? 0 : val);
                  }}
                />
              </div>
            {:else if item.type === "slider"}
              <div class="setting-item-row">
                <span class="setting-label">{item.text}</span>
                <div class="slider-group">
                  <input
                    type="range"
                    class="setting-range"
                    min={item.min ?? 0}
                    max={item.max ?? 100}
                    step={item.step ?? (item.var_type === "float" ? 0.1 : 1)}
                    value={getItemValue(item) ?? 0}
                    on:input={(e) => {
                      const val =
                        item.var_type === "float"
                          ? parseFloat(e.currentTarget.value)
                          : parseInt(e.currentTarget.value, 10);
                      updateSetting(item, isNaN(val) ? 0 : val);
                    }}
                  />
                  <span class="range-val">{getItemValue(item) ?? 0}</span>
                </div>
              </div>
            {:else if item.type === "color"}
              <div class="setting-item-row">
                <span class="setting-label">{item.text}</span>
                <div class="color-picker-group">
                  <input
                    type="color"
                    class="color-picker"
                    value={getHex6(getItemValue(item))}
                    on:change={(e) =>
                      updateSetting(item, e.currentTarget.value)}
                  />
                  <input
                    type="text"
                    class="setting-input color-text"
                    value={getItemValue(item) ?? ""}
                    on:change={(e) =>
                      updateSetting(item, e.currentTarget.value)}
                  />
                </div>
              </div>
            {:else if item.type === "list"}
              <div class="setting-item-col">
                <span class="setting-label">{item.text}</span>
                <div class="list-container">
                  {#each getListValue(item) as entry, idx}
                    <div class="list-entry-row">
                      <input
                        type="text"
                        class="setting-input"
                        value={entry}
                        on:change={(e) =>
                          updateListEntry(item, idx, e.currentTarget.value)}
                      />
                      <button
                        class="btn-sm"
                        on:click={() => removeListEntry(item, idx)}
                      >
                        Remove
                      </button>
                    </div>
                  {/each}
                  <div class="list-add-row">
                    <input
                      type="text"
                      class="setting-input"
                      placeholder="Add item..."
                      bind:value={newListItemInputs[item.key]}
                      on:keydown={(e) => {
                        if (e.key === "Enter") addListEntry(item);
                      }}
                    />
                    <button class="btn-sm" on:click={() => addListEntry(item)}
                      >Add</button
                    >
                  </div>
                </div>
              </div>
            {:else if item.type === "button"}
              <div class="setting-item-row">
                <span class="setting-label">{item.text}</span>
                <button
                  class="btn-action"
                  on:click={() => runModFunction(item)}
                >
                  Run Function
                </button>
              </div>
            {/if}
          {/each}
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  .settings-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    background: #fff;
    color: #000;
  }

  .settings-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 8px;
    border-bottom: 1px solid #000;
    font-size: 13px;
  }

  .toolbar-title h3 {
    margin: 0;
    font-size: 15px;
    font-weight: bold;
  }

  .toolbar-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .btn-refresh {
    background: #fff;
    color: #000;
    border: 1px solid #000;
    padding: 2px 8px;
    font-size: 12px;
    cursor: pointer;
  }

  .btn-refresh:active {
    background: #000;
    color: #fff;
  }

  .settings-body {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .settings-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
    border: 1px solid #000;
    padding: 10px;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #000;
    padding-bottom: 4px;
  }

  .section-title {
    margin: 0;
    font-size: 13px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .btn-reset {
    background: #fff;
    color: #000;
    border: 1px solid #000;
    padding: 1px 6px;
    font-size: 11px;
    cursor: pointer;
  }

  .btn-reset:active {
    background: #000;
    color: #fff;
  }

  .section-content {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .setting-item-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    cursor: pointer;
  }

  .setting-item-checkbox input[type="checkbox"] {
    cursor: pointer;
  }

  .setting-item-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-size: 13px;
  }

  .setting-item-col {
    display: flex;
    flex-direction: column;
    gap: 6px;
    font-size: 13px;
  }

  .setting-label {
    font-size: 13px;
  }

  .setting-input {
    background: #fff;
    color: #000;
    border: 1px solid #000;
    padding: 3px 6px;
    font-size: 13px;
    flex: 1;
    max-width: 280px;
  }

  .setting-number {
    max-width: 100px;
  }

  .setting-select {
    background: #fff;
    color: #000;
    border: 1px solid #000;
    padding: 3px 6px;
    font-size: 13px;
    max-width: 280px;
  }

  .slider-group {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    max-width: 280px;
  }

  .setting-range {
    flex: 1;
    cursor: pointer;
  }

  .range-val {
    font-size: 12px;
    min-width: 32px;
    text-align: right;
    font-family: monospace;
  }

  .color-picker-group {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    max-width: 280px;
  }

  .color-picker {
    width: 28px;
    height: 24px;
    padding: 0;
    border: 1px solid #000;
    background: none;
    cursor: pointer;
  }

  .color-text {
    max-width: 120px;
  }

  .list-container {
    display: flex;
    flex-direction: column;
    gap: 6px;
    border: 1px solid #000;
    padding: 6px;
  }

  .list-entry-row,
  .list-add-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .btn-sm,
  .btn-action {
    background: #fff;
    color: #000;
    border: 1px solid #000;
    padding: 2px 8px;
    font-size: 12px;
    cursor: pointer;
  }

  .btn-sm:active,
  .btn-action:active {
    background: #000;
    color: #fff;
  }
</style>
