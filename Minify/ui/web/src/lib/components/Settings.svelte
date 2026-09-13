<script lang="ts">
  import { onMount } from "svelte";
  import { t } from "../i18n";

  export let active: boolean = false;
  export let onSettingChange: ((key: string, value: any) => void) | undefined = undefined;

  interface SettingItem {
    key: string;
    text: string;
    type: string;
    default?: any;
    mod?: string | null;
    mod_display_name?: string | null;
    plugin?: string | null;
    force?: boolean;
    items?: Array<string | { value: string; label: string }>;
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
      if (window.pywebview?.api?.set_setting) {
        await window.pywebview.api.set_setting(item.key, newValue);
      }
      if (onSettingChange) {
        onSettingChange(item.key, newValue);
      }
    }
  }

  async function runModFunction(item: SettingItem) {
    if (item.mod && window.pywebview?.api?.run_mod_function) {
      await window.pywebview.api.run_mod_function(item.mod, item.key);
    } else if (item.plugin && window.pywebview?.api?.call_plugin_api) {
      await window.pywebview.api.call_plugin_api(item.plugin, item.key);
    }
  }

  function getItemValue(item: SettingItem, currentValues = values): any {
    return currentValues[item.key] ?? item.default;
  }

  function getListValue(item: SettingItem, currentValues = values): string[] {
    const val = getItemValue(item, currentValues);
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
      const isNative = sectionTitle === "Application Settings" || !items[0]?.mod;
      if (isNative) {
        if (window.pywebview?.api?.reset_native_settings) {
          await window.pywebview.api.reset_native_settings();
          if (onSettingChange) {
            onSettingChange("theme", "light");
            onSettingChange("locale", "en");
            onSettingChange("output_locale", "english");
          }
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

  $: getSettingLabel = (item: SettingItem): string => {
    if (item.text) {
      return item.text.startsWith("&") ? $t(item.text) : item.text;
    }
    return item.key ? $t(`setting_${item.key}`) : "";
  };

  $: sections = (() => {
    const map = new Map<string, SettingItem[]>();
    for (const item of schema) {
      const secName = item.plugin
        ? `Plugin: ${item.plugin}`
        : item.mod
          ? item.mod_display_name || item.mod
          : "Application Settings";
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
      <h3>{$t("title_settings")}</h3>
    </div>
    <div class="toolbar-controls">
      <button class="btn-refresh" on:click={loadSettings}>
        {$t("button_refresh")}
      </button>
    </div>
  </div>

  <div class="settings-body">
    {#each sections as [sectionTitle, items]}
      <div class="settings-section">
        <div class="section-header">
          <h4 class="section-title">
            {sectionTitle === "Application Settings" ? $t("section_application_settings") : sectionTitle}
          </h4>
          <button class="btn-reset" on:click={() => resetSection(sectionTitle, items)}>
            {$t("button_reset")}
          </button>
        </div>
        <div class="section-content">
          {#each items as item (item.key)}
            {#if item.type === "checkbox"}
              <label class="setting-item-checkbox">
                <input
                  type="checkbox"
                  checked={Boolean(getItemValue(item, values))}
                  on:change={(e) => updateSetting(item, e.currentTarget.checked)}
                />
                <span class="setting-text">{getSettingLabel(item)}</span>
              </label>
            {:else if item.type === "inputbox" || item.type === "text"}
              <div class="setting-item-row">
                <span class="setting-label">{getSettingLabel(item)}</span>
                <input
                  type="text"
                  class="setting-input"
                  value={getItemValue(item, values) ?? ""}
                  on:change={(e) => updateSetting(item, e.currentTarget.value)}
                />
              </div>
            {:else if item.type === "combo"}
              <div class="setting-item-row">
                <span class="setting-label">{getSettingLabel(item)}</span>
                <select
                  class="setting-select"
                  value={getItemValue(item, values) ?? ""}
                  on:change={(e) => updateSetting(item, e.currentTarget.value)}
                >
                  {#each item.items || [] as option}
                    {#if typeof option === "object" && option !== null}
                      <option value={option.value}>{option.label}</option>
                    {:else}
                      <option value={option}>{option}</option>
                    {/if}
                  {/each}
                </select>
              </div>
            {:else if item.type === "number"}
              <div class="setting-item-row">
                <span class="setting-label">{getSettingLabel(item)}</span>
                <input
                  type="number"
                  class="setting-input setting-number"
                  step={item.step ?? (item.var_type === "float" ? 0.1 : 1)}
                  min={item.min ?? undefined}
                  max={item.max ?? undefined}
                  value={getItemValue(item, values) ?? 0}
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
                <span class="setting-label">{getSettingLabel(item)}</span>
                <div class="slider-group">
                  <input
                    type="range"
                    class="setting-range"
                    min={item.min ?? 0}
                    max={item.max ?? 100}
                    step={item.step ?? (item.var_type === "float" ? 0.1 : 1)}
                    value={getItemValue(item, values) ?? 0}
                    on:input={(e) => {
                      const val =
                        item.var_type === "float"
                          ? parseFloat(e.currentTarget.value)
                          : parseInt(e.currentTarget.value, 10);
                      updateSetting(item, isNaN(val) ? 0 : val);
                    }}
                  />
                  <span class="range-val">{getItemValue(item, values) ?? 0}</span>
                </div>
              </div>
            {:else if item.type === "color"}
              <div class="setting-item-row">
                <span class="setting-label">{getSettingLabel(item)}</span>
                <div class="color-picker-group">
                  <input
                    type="color"
                    class="color-picker"
                    value={getHex6(getItemValue(item, values))}
                    on:change={(e) => updateSetting(item, e.currentTarget.value)}
                  />
                  <input
                    type="text"
                    class="setting-input color-text"
                    value={getItemValue(item, values) ?? ""}
                    on:change={(e) => updateSetting(item, e.currentTarget.value)}
                  />
                </div>
              </div>
            {:else if item.type === "list"}
              <div class="setting-item-col">
                <span class="setting-label">{getSettingLabel(item)}</span>
                <div class="list-container">
                  {#each getListValue(item, values) as entry, idx}
                    <div class="list-entry-row">
                      <input
                        type="text"
                        class="setting-input"
                        value={entry}
                        on:change={(e) => updateListEntry(item, idx, e.currentTarget.value)}
                      />
                      <button class="btn-sm" on:click={() => removeListEntry(item, idx)}>
                        {$t("button_remove")}
                      </button>
                    </div>
                  {/each}
                  <div class="list-add-row">
                    <input
                      type="text"
                      class="setting-input"
                      placeholder={$t("placeholder_add_item")}
                      bind:value={newListItemInputs[item.key]}
                      on:keydown={(e) => {
                        if (e.key === "Enter") addListEntry(item);
                      }}
                    />
                    <button class="btn-sm" on:click={() => addListEntry(item)}>
                      {$t("button_add")}
                    </button>
                  </div>
                </div>
              </div>
            {:else if item.type === "button"}
              <div class="setting-item-row">
                <span class="setting-label">{getSettingLabel(item)}</span>
                <button class="btn-action" on:click={() => runModFunction(item)}> Run Function </button>
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
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #000);
  }

  .settings-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 38px;
    padding: 0 8px;
    border-bottom: 1px solid var(--border-color, #000);
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

  .btn-refresh {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 8px;
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    border: 1px solid var(--btn-border, #000);
    font-size: 12px;
    line-height: 1;
    cursor: pointer;
    box-sizing: border-box;
  }

  .btn-refresh:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .btn-refresh:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
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
    border: 1px solid var(--border-color, #000);
    background: var(--bg-primary, #fff);
    padding: 10px;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color, #000);
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
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    border: 1px solid var(--btn-border, #000);
    padding: 1px 6px;
    font-size: 11px;
    cursor: pointer;
  }

  .btn-reset:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .btn-reset:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
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
    background: var(--input-bg, #fff);
    color: var(--input-text, #000);
    border: 1px solid var(--input-border, #000);
    padding: 3px 6px;
    font-size: 13px;
    flex: 1;
    max-width: 280px;
  }

  .setting-number {
    max-width: 100px;
  }

  .setting-select {
    background: var(--input-bg, #fff);
    color: var(--input-text, #000);
    border: 1px solid var(--input-border, #000);
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
    border: 1px solid var(--input-border, #000);
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
    border: 1px solid var(--border-color, #000);
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
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    border: 1px solid var(--btn-border, #000);
    padding: 2px 8px;
    font-size: 12px;
    cursor: pointer;
  }

  .btn-sm:hover,
  .btn-action:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .btn-sm:active,
  .btn-action:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }
</style>
