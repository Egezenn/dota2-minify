"use strict";
var XmlInspector;
(function (XmlInspector) {
    function buildXmlFromPanel(panel, depth, ignoreBlacklist = false) {
        const indent = "\t".repeat(depth);
        const tag = panel.paneltype || "Panel";
        let attrs = "";
        if (panel.id)
            attrs += ` id="${panel.id}"`;
        if (panel.actualclassnames)
            attrs += ` class="${panel.actualclassnames}"`;
        const globalKeys = ["visible", "hittest", "hittestchildren", "enabled", "layoutfile", "mousedown", "default", "actualuiscale_x", "actualuiscale_y"];
        const tagAttributes = {
            "Label": ["text", "html"],
            "Image": ["src", "scaling"],
            "DOTAScenePanel": ["map", "camera", "particleonly"],
            "DOTAParticleScenePanel": ["fov", "cameraOrigin", "lookAt", "particleonly", "particleName"],
            "TextButton": ["text", "unlocalized"],
            "RadioButton": ["group", "text", "checked"],
            "DOTAHeroImage": ["heroimagestyle", "scaling"],
            "DOTAUIEconSetPreview": ["itemdef", "drawbackground", "suppress-intro-effects"],
            "ToggleButton": ["text", "unlocalized", "checked"],
            "AnimatedImageStrip": ["src", "frametime", "framewidth", "defaultframe"],
            "DOTASettingsKeyBinder": ["bind", "text"],
            "DOTATeamImage": ["teamimagestyle", "teamid"],
            "DOTASettingsCheckbox": ["convar", "text", "checked"],
            "MoviePanel": ["autoplay", "repeat", "src"],
            "DOTAAbilityImage": ["abilityname", "showtooltip", "scaling"],
            "ProgressBar": ["value", "min", "max", "intValue"],
            "TextEntry": ["placeholder", "oninputsubmit", "multiline", "intValue"],
            "DropDown": ["oninputsubmit", "menuclass", "ability_index", "intValue"],
            "DOTAItemImage": ["scaling", "showtooltip"],
            "DOTASettingsSlider": ["convar", "min", "max", "text", "percentage", "intValue"],
            "AsyncDataPanel": ["state", "loading-text", "error-text"]
        };
        const keysToCheck = [...globalKeys];
        const specificKeys = tagAttributes[tag];
        if (specificKeys) {
            keysToCheck.push(...specificKeys);
        }
        for (const key of keysToCheck) {
            try {
                const val = panel[key];
                if (val === undefined || val === null || val === "" || typeof val === "function" || typeof val === "object")
                    continue;
                // Skip default values
                if (key === "visible" && (val === true || val === "true"))
                    continue;
                if (key === "hittest" && (val === true || val === "true"))
                    continue;
                if (key === "hittestchildren" && (val === true || val === "true"))
                    continue;
                if (key === "enabled" && (val === true || val === "true"))
                    continue;
                if (key.indexOf("actualuiscale_") === 0 && (val === 1 || val === "1" || val === 1.0))
                    continue;
                const strVal = String(val);
                const escapedVal = strVal.replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                attrs += ` ${key}="${escapedVal}"`;
            }
            catch (e) {
                // Ignore properties that throw on access
            }
        }
        const childCount = panel.GetChildCount();
        if (childCount === 0) {
            return `${indent}<${tag}${attrs} />\n`;
        }
        let xml = `${indent}<${tag}${attrs}>\n`;
        for (let i = 0; i < childCount; i++) {
            const child = panel.GetChild(i);
            if (child && (ignoreBlacklist || !XmlInspector.isPanelBlacklisted(child))) {
                xml += buildXmlFromPanel(child, depth + 1, ignoreBlacklist);
            }
        }
        xml += `${indent}</${tag}>\n`;
        return xml;
    }
    XmlInspector.buildXmlFromPanel = buildXmlFromPanel;
    function buildSelectorString(panel) {
        const tag = panel.paneltype || "Panel";
        const id = panel.id || "";
        const classes = (panel.actualclassnames || "").split(" ");
        let sel = tag;
        if (id)
            sel += "#" + id;
        for (const cls of classes) {
            if (cls)
                sel += "." + cls;
        }
        return sel;
    }
    XmlInspector.buildSelectorString = buildSelectorString;
    function buildPropertiesString(panel) {
        let s = "";
        s += `Selector: ${buildSelectorString(panel)}\n`;
        s += `Visible:  ${panel.visible}\n`;
        s += `HitTest:  ${panel.hittest}\n`;
        s += `Children: ${panel.GetChildCount()}\n`;
        s += "\n--- XML ---\n";
        s += buildXmlFromPanel(panel, 0);
        return s;
    }
    XmlInspector.buildPropertiesString = buildPropertiesString;
    function getRootPanel() {
        let ctx = $.GetContextPanel();
        while (ctx) {
            const parent = ctx.GetParent();
            if (!parent)
                break;
            ctx = parent;
        }
        return ctx;
    }
    XmlInspector.getRootPanel = getRootPanel;
})(XmlInspector || (XmlInspector = {}));

var XmlInspector;
(function (XmlInspector) {
    let popupVisible = false;
    function togglePopup(ignoreBlacklist = false) {
        if (popupVisible) {
            hidePopup();
        }
        else {
            popupVisible = true;
            const popup = $("#XmlInspectorPopup");
            if (!popup)
                return;
            popup.visible = true;
            popup.hittest = true;
            const title = $("#XmlInspectorTitle");
            if (title)
                title.text = ignoreBlacklist
                    ? "XML Inspector (All)"
                    : "XML Inspector (Filtered)";
            XmlInspector.setCurrentInspectPanel(null);
            const entry = $("#XmlInspectorEntry");
            if (!entry)
                return;
            const ctx = XmlInspector.getRootPanel();
            if (!ctx)
                return;
            entry.text = XmlInspector.buildXmlFromPanel(ctx, 0, ignoreBlacklist);
        }
    }
    XmlInspector.togglePopup = togglePopup;
    function showPropertiesPopup(text, panel) {
        popupVisible = true;
        const popup = $("#XmlInspectorPopup");
        if (popup) {
            popup.visible = true;
            popup.hittest = true;
        }
        const title = $("#XmlInspectorTitle");
        if (title)
            title.text = "Element Inspector";
        const entry = $("#XmlInspectorEntry");
        if (entry)
            entry.text = text;
        XmlInspector.setCurrentInspectPanel(panel || null);
    }
    XmlInspector.showPropertiesPopup = showPropertiesPopup;
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

var XmlInspector;
(function (XmlInspector) {
    const INSPECTOR_IDS = new Set([
        "XmlInspectorButtonsContainer",
        "XmlInspectorBtn",
        "XmlInspectorAllBtn",
        "XmlInspectBtn",
        "XmlBlacklistBtn",
        "XmlInspectorPopup",
        "XmlInspectorOverlay",
        "XmlInspectorContainer",
        "XmlInspectorTitle",
        "XmlInspectorCloseBtn",
        "XmlInspectorEntry",
        "XmlInspectorBlacklistBtnPopup",
    ]);
    let inspectMode = false;
    let hittestStates = [];
    let pendingQueue = [];
    const BATCH_SIZE = 50;
    function processBatch() {
        if (!inspectMode) {
            pendingQueue = [];
            return;
        }
        const count = Math.min(BATCH_SIZE, pendingQueue.length);
        for (let b = 0; b < count; b++) {
            const panel = pendingQueue[b];
            for (let i = 0; i < panel.GetChildCount(); i++) {
                const child = panel.GetChild(i);
                if (!child || INSPECTOR_IDS.has(child.id))
                    continue;
                if (XmlInspector.isPanelBlacklisted(child)) {
                    pendingQueue.push(child);
                    continue;
                }
                hittestStates.push({
                    panel: child,
                    hittest: child.hittest,
                    hittestchildren: child.hittestchildren,
                });
                child.hittest = true;
                ((c) => {
                    c.SetPanelEvent("oncontextmenu", () => {
                        if (!inspectMode)
                            return;
                        const props = XmlInspector.buildPropertiesString(c);
                        stopInspectMode();
                        XmlInspector.showPropertiesPopup(props, c);
                    });
                })(child);
                pendingQueue.push(child);
            }
        }
        pendingQueue.splice(0, count);
        if (pendingQueue.length > 0) {
            $.Schedule(0, processBatch);
        }
    }
    function registerListeners(root) {
        pendingQueue = [root];
        processBatch();
    }
    function restoreHittest() {
        for (const state of hittestStates) {
            if (state.panel.IsValid()) {
                state.panel.hittest = state.hittest;
                state.panel.hittestchildren = state.hittestchildren;
            }
        }
        hittestStates = [];
    }
    function stopInspectMode() {
        inspectMode = false;
        const btn = $("#XmlInspectBtn");
        if (btn)
            btn.SetHasClass("Active", false);
        restoreHittest();
    }
    function toggleInspectMode() {
        const btn = $("#XmlInspectBtn");
        if (!btn)
            return;
        if (!inspectMode) {
            inspectMode = true;
            btn.SetHasClass("Active", true);
            XmlInspector.hidePopup();
            const ctx = XmlInspector.getRootPanel();
            if (ctx)
                registerListeners(ctx);
        }
        else {
            stopInspectMode();
        }
    }
    XmlInspector.toggleInspectMode = toggleInspectMode;
})(XmlInspector || (XmlInspector = {}));

var XmlInspector;
(function (XmlInspector) {
    XmlInspector.DEFAULT_BLACKLIST = [
        "Button#BlurBackground",
        "Button#DashboardPagesBlocker",
        "DOTAContextMenuManager#ContextMenuManager",
        "DOTACustomLobby#CustomLobby",
        "DOTADashboardPopupManager#DashboardPopupManager",
        "DOTAHelpTipsManager#HelpTipsManager",
        "DOTAHomePage#DOTAHomePage",
        "DOTAPlay#Play",
        "DOTATooltipManager#Tooltips",
        "DOTAToolTipManager#Tooltips",
        "PageManager#DashboardPages",
        "Panel#ChatMainPanel",
        "Panel#DashboardForeground",
        "Panel#DimBackground",
        "Panel#FriendMenuContainer",
        "Panel#FullscreenVideoContainer",
        "Panel#NotificationsContainer",
        "Panel#PlusMenuContainer",
        "Panel#RecentArmoryItemsMenuContainer",
        "Panel#ShardsMenuContainer",
        "Panel#TipTargets",
        "Panel#TodayPages",
        "PopupManager#PopupManager",
        "ToastManager#ToastManager",
    ];
})(XmlInspector || (XmlInspector = {}));

var XmlInspector;
(function (XmlInspector) {
    const MAX_ROWS = 32;
    const blacklist = XmlInspector.DEFAULT_BLACKLIST.map((selector) => ({
        selector,
    }));
    let blacklistMode = "text";
    let initialized = false;
    let currentInspectPanel = null;
    const rowInputs = [];
    const rowPanels = [];
    function initBlacklistUI() {
        if (initialized)
            return;
        initialized = true;
        const list = $("#BlacklistList");
        if (!list)
            return;
        for (let i = 0; i < MAX_ROWS; i++) {
            const row = $.CreatePanel("Panel", list, "");
            row.AddClass("BlacklistRow");
            row.visible = false;
            const input = $.CreatePanel("TextEntry", row, "");
            input.AddClass("BlacklistInput");
            const removeBtn = $.CreatePanel("Button", row, "");
            removeBtn.AddClass("BlacklistRemoveBtn");
            const removeLabel = $.CreatePanel("Label", removeBtn, "");
            removeLabel.text = "X";
            const idx = i;
            removeBtn.SetPanelEvent("onactivate", () => {
                blacklist.splice(idx, 1);
                syncBlacklistUI();
            });
            input.SetPanelEvent("onvaluechanged", () => {
                if (idx < blacklist.length) {
                    blacklist[idx].selector = input.text;
                }
            });
            rowPanels.push(row);
            rowInputs.push(input);
        }
        const addBtn = $.CreatePanel("Button", list, "");
        addBtn.AddClass("BlacklistAddBtn");
        const addLabel = $.CreatePanel("Label", addBtn, "");
        addLabel.text = "+ Add";
        addBtn.SetPanelEvent("onactivate", () => {
            if (blacklist.length < MAX_ROWS) {
                blacklist.push({ selector: "" });
                syncBlacklistUI();
            }
        });
        const rawEntry = $("#BlacklistRawEntry");
        if (rawEntry) {
            const initialText = blacklist.map((e) => e.selector).join("\n");
            rawEntry.text = initialText;
            rawEntry.SetPanelEvent("onvaluechanged", () => {
                if (blacklistMode !== "text")
                    return;
                const lines = rawEntry.text
                    .split("\n")
                    .map((s) => s.trim())
                    .filter(Boolean);
                blacklist.length = 0;
                for (const line of lines) {
                    if (blacklist.length < MAX_ROWS) {
                        blacklist.push({ selector: line });
                    }
                }
            });
        }
    }
    XmlInspector.initBlacklistUI = initBlacklistUI;
    function setCurrentInspectPanel(panel) {
        currentInspectPanel = panel;
        refreshBlacklistButton();
    }
    XmlInspector.setCurrentInspectPanel = setCurrentInspectPanel;
    function isPanelBlacklisted(panel) {
        const selector = XmlInspector.buildSelectorString(panel);
        return blacklist.some((e) => e.selector === selector);
    }
    XmlInspector.isPanelBlacklisted = isPanelBlacklisted;
    function toggleBlacklistEntry() {
        if (!currentInspectPanel)
            return;
        const selector = XmlInspector.buildSelectorString(currentInspectPanel);
        const idx = blacklist.findIndex((e) => e.selector === selector);
        if (idx >= 0) {
            blacklist.splice(idx, 1);
        }
        else {
            blacklist.push({ selector });
        }
        refreshBlacklistButton();
        syncBlacklistUI();
    }
    XmlInspector.toggleBlacklistEntry = toggleBlacklistEntry;
    function refreshBlacklistButton() {
        const btn = $("#XmlInspectorBlacklistBtnPopup");
        if (!btn)
            return;
        if (!currentInspectPanel) {
            btn.visible = false;
            return;
        }
        btn.visible = true;
        const selector = XmlInspector.buildSelectorString(currentInspectPanel);
        const inList = blacklist.some((e) => e.selector === selector);
        const label = btn.GetChild(0);
        if (label)
            label.text = inList ? "- BL" : "+ BL";
    }
    function setBlacklistMode(mode) {
        blacklistMode = mode;
        refreshModeButtons();
        syncBlacklistUI();
    }
    XmlInspector.setBlacklistMode = setBlacklistMode;
    function refreshModeButtons() {
        const textBtn = $("#BlacklistModeText");
        const xmlBtn = $("#BlacklistModeXml");
        if (textBtn)
            textBtn.SetHasClass("Active", blacklistMode === "text");
        if (xmlBtn)
            xmlBtn.SetHasClass("Active", blacklistMode === "xml");
    }
    function hideBlacklistPanel() {
        const popup = $("#XmlInspectorBlacklistPopup");
        if (popup) {
            popup.visible = false;
            popup.hittest = false;
        }
    }
    XmlInspector.hideBlacklistPanel = hideBlacklistPanel;
    function toggleBlacklistPanel() {
        const popup = $("#XmlInspectorBlacklistPopup");
        if (!popup)
            return;
        if (popup.visible) {
            popup.visible = false;
            popup.hittest = false;
        }
        else {
            initBlacklistUI();
            popup.visible = true;
            popup.hittest = true;
            refreshModeButtons();
            syncBlacklistUI();
        }
    }
    XmlInspector.toggleBlacklistPanel = toggleBlacklistPanel;
    function syncBlacklistUI() {
        const rawEntry = $("#BlacklistRawEntry");
        const list = $("#BlacklistList");
        if (blacklistMode === "text") {
            if (rawEntry) {
                rawEntry.visible = true;
                const newText = blacklist.map((e) => e.selector).join("\n");
                if (rawEntry.text !== newText) {
                    rawEntry.text = newText;
                }
            }
            if (list)
                list.visible = false;
        }
        else {
            if (rawEntry)
                rawEntry.visible = false;
            if (list)
                list.visible = true;
            for (let i = 0; i < MAX_ROWS; i++) {
                const row = rowPanels[i];
                if (i < blacklist.length) {
                    const entry = blacklist[i];
                    row.visible = true;
                    rowInputs[i].text = entry.selector;
                }
                else {
                    row.visible = false;
                }
            }
        }
    }
})(XmlInspector || (XmlInspector = {}));

function ToggleXmlInspectorPopup() {
    XmlInspector.togglePopup(false);
}
function ToggleXmlInspectorAllPopup() {
    XmlInspector.togglePopup(true);
}
function ToggleInspectMode() {
    XmlInspector.toggleInspectMode();
}
function ToggleBlacklistPanel() {
    XmlInspector.toggleBlacklistPanel();
}
function ToggleBlacklistEntry() {
    XmlInspector.toggleBlacklistEntry();
}
function SetBlacklistModeText() {
    XmlInspector.setBlacklistMode("text");
}
function SetBlacklistModeXml() {
    XmlInspector.setBlacklistMode("xml");
}
$.Schedule(0, () => {
    XmlInspector.hidePopup();
    XmlInspector.hideBlacklistPanel();
    const popup = $("#XmlInspectorPopup");
    if (popup) {
        $.RegisterKeyBind(popup, "key_escape", () => {
            XmlInspector.hidePopup();
        });
    }
    const blPopup = $("#XmlInspectorBlacklistPopup");
    if (blPopup) {
        $.RegisterKeyBind(blPopup, "key_escape", () => {
            XmlInspector.toggleBlacklistPanel();
        });
    }
});
