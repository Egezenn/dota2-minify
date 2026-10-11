"use strict";
var XmlInspector;
(function (XmlInspector) {
  function buildXmlFromPanel(panel, depth = 0) {
    const indent = "\t".repeat(depth);
    const tag = panel.paneltype || "Panel";
    let attrs = "";
    if (panel.id) attrs += ` id="${panel.id}"`;
    if (panel.actualclassnames) attrs += ` class="${panel.actualclassnames}"`;

    const globalKeys = [
      "visible",
      "hittest",
      "hittestchildren",
      "enabled",
      "layoutfile",
      "mousedown",
      "default",
      "actualuiscale_x",
      "actualuiscale_y",
    ];

    const tagAttributes = {
      Label: ["text", "html"],
      Image: ["src", "scaling"],
      DOTAScenePanel: ["map", "camera", "particleonly"],
      DOTAParticleScenePanel: ["fov", "cameraOrigin", "lookAt", "particleonly", "particleName"],
      TextButton: ["text", "unlocalized"],
      RadioButton: ["group", "text", "checked"],
      DOTAHeroImage: ["heroimagestyle", "scaling"],
      DOTAUIEconSetPreview: ["itemdef", "drawbackground", "suppress-intro-effects"],
      ToggleButton: ["text", "unlocalized", "checked"],
      AnimatedImageStrip: ["src", "frametime", "framewidth", "defaultframe"],
      DOTASettingsKeyBinder: ["bind", "text"],
      DOTATeamImage: ["teamimagestyle", "teamid"],
      DOTASettingsCheckbox: ["convar", "text", "checked"],
      MoviePanel: ["autoplay", "repeat", "src"],
      DOTAAbilityImage: ["abilityname", "showtooltip", "scaling"],
      ProgressBar: ["value", "min", "max", "intValue"],
      TextEntry: ["placeholder", "oninputsubmit", "multiline", "intValue"],
      DropDown: ["oninputsubmit", "menuclass", "ability_index", "intValue"],
      DOTAItemImage: ["scaling", "showtooltip"],
      DOTASettingsSlider: ["convar", "min", "max", "text", "percentage", "intValue"],
      AsyncDataPanel: ["state", "loading-text", "error-text"],
    };

    const keysToCheck = [...globalKeys];
    const specificKeys = tagAttributes[tag];
    if (specificKeys) keysToCheck.push(...specificKeys);

    for (const key of keysToCheck) {
      try {
        const val = panel[key];
        if (val === undefined || val === null || val === "" || typeof val === "function" || typeof val === "object") continue;
        if (key === "visible" && (val === true || val === "true")) continue;
        if (key === "hittest" && (val === true || val === "true")) continue;
        if (key === "hittestchildren" && (val === true || val === "true")) continue;
        if (key === "enabled" && (val === true || val === "true")) continue;
        if (key.indexOf("actualuiscale_") === 0 && (val === 1 || val === "1" || val === 1.0)) continue;
        const strVal = String(val);
        const escapedVal = strVal.replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        attrs += ` ${key}="${escapedVal}"`;
      } catch (e) {
        // Ignore properties that throw on access.
      }
    }

    const childCount = panel.GetChildCount();
    if (childCount === 0) {
      return `${indent}<${tag}${attrs} />\n`;
    }

    let xml = `${indent}<${tag}${attrs}>\n`;
    for (let i = 0; i < childCount; i++) {
      const child = panel.GetChild(i);
      if (child) xml += buildXmlFromPanel(child, depth + 1);
    }
    xml += `${indent}</${tag}>\n`;
    return xml;
  }
  XmlInspector.buildXmlFromPanel = buildXmlFromPanel;

  function getRootPanel() {
    let ctx = $.GetContextPanel();
    while (ctx) {
      const parent = ctx.GetParent();
      if (!parent) break;
      ctx = parent;
    }
    return ctx;
  }
  XmlInspector.getRootPanel = getRootPanel;

  let popupVisible = false;
  function togglePopup() {
    if (popupVisible) {
      hidePopup();
      return;
    }

    popupVisible = true;
    const popup = $("#XmlInspectorPopup");
    if (!popup) return;
    popup.visible = true;
    popup.hittest = true;

    const entry = $("#XmlInspectorEntry");
    if (!entry) return;

    const root = XmlInspector.getRootPanel();
    if (!root) return;
    entry.text = XmlInspector.buildXmlFromPanel(root, 0);
  }
  XmlInspector.togglePopup = togglePopup;

  function hidePopup() {
    const popup = $("#XmlInspectorPopup");
    if (popup) {
      popupVisible = false;
      popup.visible = false;
      popup.hittest = false;
    }
  }
  XmlInspector.hidePopup = hidePopup;
})(XmlInspector || (XmlInspector = {}));

function ToggleXmlInspectorPopup() {
  XmlInspector.togglePopup();
}

$.Schedule(0, () => {
  XmlInspector.hidePopup();
  const popup = $("#XmlInspectorPopup");
  if (popup) {
    $.RegisterKeyBind(popup, "key_escape", () => {
      XmlInspector.hidePopup();
    });
  }
});
