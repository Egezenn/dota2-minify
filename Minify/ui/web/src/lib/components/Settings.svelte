<script lang="ts">
  import { onMount } from "svelte";

  export let onSettingChange: (key: string, value: boolean) => void;

  interface SettingItem {
    key: string;
    text: string;
    default: boolean;
    type: string;
  }

  let schema: SettingItem[] = [
    {
      key: "opt_into_rcs",
      text: "Opt into RCs",
      default: false,
      type: "checkbox",
    },
    {
      key: "fix_options",
      text: "Handle language option (current ID)",
      default: true,
      type: "checkbox",
    },
    {
      key: "patch_on_launch",
      text: "Run patches upon launch if required",
      default: true,
      type: "checkbox",
    },
    {
      key: "apply_for_all",
      text: "Apply everything for all users",
      default: true,
      type: "checkbox",
    },
    {
      key: "launch_dota_after_patch",
      text: "Launch Dota2 after patching",
      default: false,
      type: "checkbox",
    },
    {
      key: "kill_self_after_patch",
      text: "Close Minify after patching",
      default: false,
      type: "checkbox",
    },
    {
      key: "opt_out_vpk_metadata",
      text: "Opt-out of VPK metadata",
      default: false,
      type: "checkbox",
    },
  ];

  let values: Record<string, boolean> = {
    opt_into_rcs: false,
    fix_options: true,
    patch_on_launch: true,
    apply_for_all: true,
    launch_dota_after_patch: false,
    kill_self_after_patch: false,
    opt_out_vpk_metadata: false,
  };

  onMount(async () => {
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
  });

  function toggleSetting(key: string, checked: boolean) {
    values[key] = checked;
    values = { ...values };
    onSettingChange(key, checked);
  }
</script>

<div class="settings-container">
  <div class="settings-header">
    <h3>Application Settings</h3>
  </div>

  <div class="settings-list">
    {#each schema as item (item.key)}
      <label class="setting-item">
        <input
          type="checkbox"
          checked={values[item.key] ?? item.default}
          on:change={(e) => toggleSetting(item.key, e.currentTarget.checked)}
        />
        <span class="setting-text">{item.text}</span>
      </label>
    {/each}
  </div>
</div>

<style>
  .settings-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow-y: auto;
    padding: 16px;
    gap: 16px;
  }

  .settings-header h3 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
    border-bottom: 1px solid #ccc;
    padding-bottom: 8px;
  }

  .settings-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .setting-item {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    cursor: pointer;
    user-select: none;
    padding: 6px 8px;
    border-radius: 4px;
    transition: background-color 0.15s ease;
  }

  .setting-item:hover {
    background-color: #f5f5f5;
  }

  .setting-item input[type="checkbox"] {
    width: 16px;
    height: 16px;
    cursor: pointer;
  }

  .setting-text {
    color: #333;
  }
</style>
