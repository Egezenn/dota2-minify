<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { marked } from "marked";
  import markedAlert from "marked-alert";
  import hljs from "highlight.js";
  import FileTree from "./FileTree.svelte";
  import { t } from "../i18n";
  import { localeStore } from "../stores/locale";

  export let modName: string | null = null;
  export let onClose: () => void;

  interface ModMethod {
    name: string;
    type: "tree" | "json" | "blacklist" | "css" | "python" | "xml" | "text";
    content?: string;
    tree?: any;
    badge?: string;
    highlightedLines?: string[];
  }

  let loading = true;
  let previewLightboxOpen = false;
  let details: {
    name: string;
    display_name?: string;
    notes: string | null;
    preview: string | null;
    has_notes: boolean;
    has_preview: boolean;
    methods?: ModMethod[];
  } | null = null;

  $: displayName = details?.display_name || details?.name || modName;

  marked.setOptions({
    gfm: true,
    breaks: true,
  });

  marked.use(markedAlert());

  marked.use({
    renderer: {
      code(token: any) {
        const text = typeof token === "object" ? token.text : token;
        const lang = typeof token === "object" ? token.lang : arguments[1];
        const validLang = lang && hljs.getLanguage(lang) ? lang : undefined;
        const highlighted = validLang
          ? hljs.highlight(text, { language: validLang, ignoreIllegals: true }).value
          : escapeHtml(text || "");
        return `<pre><code class="hljs ${validLang ? `language-${validLang}` : ""}">${highlighted}</code></pre>`;
      },
    },
  });

  $: if (modName) {
    fetchDetails(modName, $localeStore.lang);
  }

  function escapeHtml(str: string): string {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function splitIntoLines(str: string): string[] {
    if (!str) return [];
    return str.split("\n");
  }

  function splitHighlightedLines(html: string): string[] {
    if (!html) return [];
    const rawLines = html.split("\n");
    const openStack: string[] = [];
    const result: string[] = [];

    for (const line of rawLines) {
      let currentLine = openStack.join("") + line;
      const tagRegex = /<\/?span[^>]*>/g;
      let match: RegExpExecArray | null;
      while ((match = tagRegex.exec(line)) !== null) {
        const tag = match[0];
        if (tag.startsWith("</")) {
          openStack.pop();
        } else {
          openStack.push(tag);
        }
      }
      for (let i = 0; i < openStack.length; i++) {
        currentLine += "</span>";
      }
      result.push(currentLine);
    }
    return result;
  }

  function highlightCode(code: string, lang: string): string {
    if (!code) return "";
    try {
      if (hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang, ignoreIllegals: true }).value;
      }
    } catch {
      // fallback
    }
    return escapeHtml(code);
  }

  function prepareMethods(methods: any[]): ModMethod[] {
    if (!methods) return [];
    return methods.map((m) => {
      let content = m.content || "";
      if (m.type === "json") {
        try {
          if (!content.includes("//") && !content.includes("/*")) {
            content = JSON.stringify(JSON.parse(content), null, 2);
          }
        } catch {
          // Preserve raw if jsonc or parse error
        }
      }

      let lines: string[] = [];
      if (m.type && m.type !== "tree" && m.type !== "blacklist" && m.type !== "text") {
        const highlighted = highlightCode(content, m.type);
        lines = splitHighlightedLines(highlighted);
      } else if (content) {
        lines = splitIntoLines(escapeHtml(content));
      }

      return {
        ...m,
        highlightedLines: lines,
      };
    });
  }

  function getMethodIcon(type: string): string {
    switch (type) {
      case "tree":
        return "📁";
      case "blacklist":
        return "🚫";
      case "json":
        return "{ }";
      case "css":
        return "🎨";
      case "python":
        return "🐍";
      case "xml":
        return "🏷️";
      default:
        return "📄";
    }
  }

  async function fetchDetails(name: string, lang?: string) {
    loading = true;
    details = null;
    try {
      if (window.pywebview?.api?.get_mod_details) {
        const res = await window.pywebview.api.get_mod_details(name, lang);
        if (res) {
          details = {
            ...res,
            methods: prepareMethods(res.methods || []),
          };
        }
      }
    } catch (err) {
      console.error("Failed to load mod details:", err);
    } finally {
      loading = false;
    }
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Escape") {
      if (previewLightboxOpen) {
        e.preventDefault();
        e.stopPropagation();
        previewLightboxOpen = false;
      } else {
        onClose();
      }
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeyDown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeyDown);
  });

  function formatNotes(markdown: string | null): string {
    if (!markdown) return "";
    return marked.parse(markdown) as string;
  }
</script>

{#if modName}
  <div
    class="modal-backdrop"
    on:click={onClose}
    role="button"
    tabindex="-1"
    on:keydown={(e) => {
      if (e.key === "Escape" && !previewLightboxOpen) {
        onClose();
      }
    }}
  >
    <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <div class="modal-card" on:click|stopPropagation role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <header class="modal-header">
        <h2 id="modal-title">{displayName}</h2>
        <button class="close-btn" type="button" on:click={onClose} aria-label={$t("button_close")}> &times; </button>
      </header>

      <div class="modal-body">
        {#if loading}
          <div class="loading-state">{$t("loading")}</div>
        {:else if details}
          {#if (details.has_preview && details.preview) || (details.has_notes && details.notes)}
            <div
              class="mod-overview"
              class:has-both={details.has_preview && details.preview && details.has_notes && details.notes}
            >
              {#if details.has_preview && details.preview}
                <div class="image-wrapper">
                  <button
                    type="button"
                    class="image-preview-btn"
                    on:click={() => (previewLightboxOpen = true)}
                    title={$t("title_click_to_preview")}
                    aria-label={$t("title_click_to_preview")}
                  >
                    <img src={details.preview} alt={`Preview for ${displayName}`} />
                  </button>
                </div>
              {/if}

              {#if details.has_notes && details.notes}
                <div class="notes-content">
                  {@html formatNotes(details.notes)}
                </div>
              {/if}
            </div>
          {/if}

          {#if details.methods && details.methods.length > 0}
            <div class="mod-methods-section">
              {#each details.methods as method (method.name)}
                <details class="mod-method-details">
                  <summary class="mod-method-summary">
                    <div class="summary-left">
                      <span class="summary-arrow">▶</span>
                      <span class="method-icon">{getMethodIcon(method.type)}</span>
                      <span class="method-name">{method.name}</span>
                    </div>
                    {#if method.badge}
                      <span class="summary-badge">{method.badge}</span>
                    {/if}
                  </summary>
                  <div class="mod-method-body">
                    {#if method.type === "tree"}
                      <FileTree node={method.tree} />
                    {:else if method.highlightedLines && method.highlightedLines.length > 0}
                      <div class="code-view">
                        <div class="code-lines">
                          {#each method.highlightedLines as line, i}
                            <div class="code-row">
                              <span class="line-no">{i + 1}</span>
                              <span class="line-content">{@html line || "&nbsp;"}</span>
                            </div>
                          {/each}
                        </div>
                      </div>
                    {:else}
                      <div class="empty-method-content">
                        {$t("label_empty_file")}
                      </div>
                    {/if}
                  </div>
                </details>
              {/each}
            </div>
          {:else if !details.has_notes && !details.has_preview}
            <div class="empty-state">{$t("label_no_mod_details")}</div>
          {/if}
        {/if}
      </div>

      <footer class="modal-footer">
        <button class="btn-close" type="button" on:click={onClose}>
          {$t("button_close")}
        </button>
      </footer>
    </div>
  </div>

  {#if previewLightboxOpen && details && details.preview}
    <div
      class="lightbox-backdrop"
      on:click|stopPropagation={() => (previewLightboxOpen = false)}
      role="button"
      tabindex="-1"
      on:keydown={(e) => {
        if (e.key === "Escape") {
          e.stopPropagation();
          e.preventDefault();
          previewLightboxOpen = false;
        }
      }}
    >
      <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
      <!-- svelte-ignore a11y-click-events-have-key-events -->
      <div class="lightbox-card" on:click|stopPropagation role="dialog" aria-modal="true" aria-label="Image Preview">
        <header class="lightbox-header">
          <span class="lightbox-title">{displayName} - {$t("label_preview")}</span>
          <button
            class="close-btn"
            type="button"
            on:click|stopPropagation={() => (previewLightboxOpen = false)}
            aria-label={$t("button_close")}
          >
            &times;
          </button>
        </header>
        <div
          class="lightbox-body"
          role="button"
          tabindex="-1"
          on:click|stopPropagation={() => (previewLightboxOpen = false)}
          on:keydown={(e) => {
            if (e.key === "Enter" || e.key === " " || e.key === "Escape") {
              e.stopPropagation();
              e.preventDefault();
              previewLightboxOpen = false;
            }
          }}
          title="Click to close"
        >
          <img src={details.preview} alt={`Preview for ${displayName}`} />
        </div>
      </div>
    </div>
  {/if}
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: var(--modal-backdrop, rgba(0, 0, 0, 0.5));
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .modal-card {
    --modal-height: 80vh;
    background: var(--modal-bg, #fff);
    width: 80vw;
    height: var(--modal-height);
    border: 1px solid var(--modal-border, #000);
    display: flex;
    flex-direction: column;
    color: var(--text-primary, #000);
    container-type: size;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 38px;
    padding: 6px 8px;
    border-bottom: 1px solid var(--border-color, #000);
    box-sizing: border-box;
  }

  .modal-header h2 {
    font-size: 15px;
    font-weight: bold;
    margin: 0;
    line-height: 1.2;
  }

  .close-btn {
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    border: 1px solid var(--btn-border, #000);
    padding: 2px 8px;
    cursor: pointer;
  }

  .close-btn:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    border-color: var(--btn-hover-border, var(--border-color, #000));
  }

  .close-btn:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }

  .modal-body {
    padding: 24px 32px;
    overflow-y: auto;
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }

  .loading-state,
  .empty-state {
    padding: 24px;
    text-align: center;
    font-size: 13px;
    color: var(--text-secondary, #666);
  }

  .mod-overview {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  @container (min-width: 700px) {
    .mod-overview.has-both {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-items: start;
      gap: 16px;
    }

    .mod-overview.has-both > * {
      min-width: 0;
    }
  }

  @media (min-width: 900px) {
    .mod-overview.has-both {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      align-items: start;
      gap: 16px;
    }

    .mod-overview.has-both > * {
      min-width: 0;
    }
  }

  .image-wrapper {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  .image-preview-btn {
    background: transparent;
    border: none;
    padding: 0;
    cursor: zoom-in;
    display: inline-flex;
    justify-content: center;
    max-width: 100%;
  }

  .image-preview-btn:hover img {
    border-color: var(--accent, #17bebe);
  }

  .image-wrapper img {
    max-width: 100%;
    max-height: 58vh;
    object-fit: contain;
    display: block;
    border: 1px solid var(--border-color, #000);
  }

  .lightbox-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.85);
    z-index: 2000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .lightbox-card {
    background: var(--modal-bg, #fff);
    border: 1px solid var(--modal-border, #000);
    display: flex;
    flex-direction: column;
    max-width: 92vw;
    max-height: 92vh;
    box-sizing: border-box;
  }

  .lightbox-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 38px;
    padding: 6px 12px;
    border-bottom: 1px solid var(--border-color, #000);
    background: var(--modal-bg, #fff);
    gap: 12px;
    box-sizing: border-box;
  }

  .lightbox-title {
    font-size: 13px;
    font-weight: bold;
    color: var(--text-primary, #000);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .lightbox-body {
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    padding: 12px;
    background: var(--terminal-bg, var(--bg-primary, #000));
    cursor: zoom-out;
  }

  .lightbox-body img {
    max-width: 88vw;
    max-height: 80vh;
    object-fit: contain;
    display: block;
  }

  .notes-content {
    width: 100%;
    border: 1px solid var(--border-color, #000);
    background: var(--bg-primary, #fff);
    color: var(--text-primary, #000);
    padding: 16px 20px;
    font-size: 13px;
    line-height: 1.5;
    overflow-wrap: break-word;
  }

  .notes-content :global(.markdown-alert) {
    border: 1px solid var(--border-color, #000);
    border-left: 4px solid var(--border-color, #000);
    padding: 6px 10px;
    margin: 6px 0;
    background: var(--bg-secondary, #fff);
    color: var(--text-primary, #000);
  }

  .notes-content :global(.markdown-alert-title) {
    font-weight: bold;
    font-size: 12px;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .notes-content :global(p) {
    margin-bottom: 0.75em;
  }

  .notes-content :global(p:last-child) {
    margin-bottom: 0;
  }

  .notes-content :global(h1),
  .notes-content :global(h2),
  .notes-content :global(h3) {
    font-size: 14px;
    font-weight: bold;
    margin-top: 12px;
    margin-bottom: 6px;
  }

  .notes-content :global(ul),
  .notes-content :global(ol) {
    padding-left: 20px;
    margin-top: 4px;
    margin-bottom: 8px;
  }

  .notes-content :global(pre) {
    border: 1px solid var(--border-color, #000);
    padding: 8px 12px;
    margin: 6px 0;
    background: var(--bg-secondary, #f8f9fa);
    color: var(--text-primary, #000);
    overflow-x: auto;
  }

  .notes-content :global(pre code) {
    border: none;
    padding: 0;
    background: transparent;
    white-space: pre;
  }

  .notes-content :global(code) {
    border: 1px solid var(--border-color, #000);
    padding: 1px 4px;
    font-family: monospace;
    font-size: 12px;
    background: var(--bg-secondary, transparent);
    color: var(--text-primary, inherit);
  }

  .mod-methods-section {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 10px;
    box-sizing: border-box;
  }

  .mod-method-details {
    width: 100%;
    border: 1px solid var(--border-color, #000);
    background: var(--bg-primary, #fff);
    box-sizing: border-box;
  }

  .mod-method-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: var(--bg-secondary, #f4f4f4);
    color: var(--text-primary, #000);
    cursor: pointer;
    font-size: 13px;
    font-weight: bold;
    user-select: none;
    list-style: none;
  }

  .mod-method-summary::-webkit-details-marker {
    display: none;
  }

  .mod-method-summary:hover {
    background: var(--btn-hover-bg, #f0f0f0);
    color: var(--text-primary, #000);
  }

  .summary-left {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .summary-arrow {
    display: inline-block;
    font-size: 9px;
    color: var(--text-muted, #888);
    transition: transform 0.15s ease;
  }

  .mod-method-details[open] .summary-arrow {
    transform: rotate(90deg);
  }

  .method-icon {
    font-size: 13px;
    display: inline-flex;
    align-items: center;
  }

  .method-name {
    font-family: var(--font-mono, monospace);
    font-size: 12px;
  }

  .summary-badge {
    font-size: 11px;
    font-weight: normal;
    color: var(--text-muted, #888);
    background: var(--bg-tertiary, #e8e8e8);
    padding: 2px 6px;
    border: 1px solid var(--border-color, #000);
    font-family: var(--font-mono, monospace);
  }

  .mod-method-body {
    border-top: 1px solid var(--border-color, #000);
    max-height: calc(var(--modal-height, 60vh) * 0.8);
    max-height: 60cqh;
    overflow: auto;
    background: var(--terminal-bg, var(--bg-primary, #fff));
  }

  .code-view {
    display: flex;
    font-family: var(--font-mono, monospace);
    font-size: 12px;
    line-height: 20px;
    color: var(--text-primary, #000);
    overflow: auto;
    background: var(--bg-secondary, #f8f9fa);
  }

  .code-lines {
    display: inline-block;
    min-width: 100%;
    padding: 6px 0;
  }

  .code-row {
    display: flex;
    align-items: flex-start;
    min-width: max-content;
  }

  .code-row:hover {
    background: var(--btn-hover-bg, rgba(0, 0, 0, 0.04));
  }

  .line-no {
    width: 44px;
    min-width: 44px;
    text-align: right;
    padding-right: 12px;
    color: var(--text-muted, #888);
    user-select: none;
    border-right: 1px solid var(--border-color, #000);
    margin-right: 12px;
    background: var(--bg-primary, #fff);
  }

  .line-content {
    flex: 1;
    white-space: pre;
    padding-right: 16px;
  }

  .empty-method-content {
    padding: 16px;
    color: var(--text-muted, #888);
    font-style: italic;
    font-family: var(--font-mono, monospace);
  }

  :global(.hljs-keyword),
  :global(.token-keyword) {
    color: var(--accent, #17bebe);
    font-weight: bold;
  }

  :global(.hljs-string),
  :global(.token-string) {
    color: #10b981;
  }

  :global(.hljs-number),
  :global(.token-number) {
    color: var(--log-warning, #d97706);
  }

  :global(.hljs-literal),
  :global(.hljs-boolean),
  :global(.token-boolean) {
    color: #a855f7;
    font-weight: bold;
  }

  :global(.hljs-null),
  :global(.token-null) {
    color: var(--text-muted, #888);
    font-style: italic;
  }

  :global(.hljs-punctuation),
  :global(.token-punctuation) {
    color: var(--text-muted, #888);
  }

  :global(.hljs-comment),
  :global(.token-comment) {
    color: var(--text-muted, #888);
    font-style: italic;
  }

  :global(.hljs-attr),
  :global(.hljs-attribute),
  :global(.token-key),
  :global(.token-attr-name) {
    color: var(--accent, #17bebe);
    font-weight: bold;
  }

  :global(.hljs-selector-tag),
  :global(.hljs-selector-class),
  :global(.hljs-selector-id),
  :global(.token-selector) {
    color: var(--accent, #17bebe);
  }

  :global(.hljs-tag),
  :global(.hljs-name),
  :global(.token-tag) {
    color: var(--accent, #17bebe);
    font-weight: bold;
  }

  :global(.hljs-title),
  :global(.hljs-title.function_),
  :global(.hljs-built_in) {
    color: #38bdf8;
  }

  :global(.hljs-property),
  :global(.token-property) {
    color: var(--text-primary, #000);
  }

  :global(.hljs-value),
  :global(.token-value) {
    color: #10b981;
  }

  .modal-footer {
    padding: 8px 12px;
    border-top: 1px solid var(--border-color, #000);
    background: var(--modal-bg, #fff);
    display: flex;
    justify-content: flex-end;
  }

  .btn-close {
    background: var(--btn-bg, #fff);
    color: var(--btn-text, #000);
    border: 1px solid var(--btn-border, #000);
    padding: 4px 12px;
    cursor: pointer;
  }

  .btn-close:active {
    background: var(--btn-active-bg, #000);
    color: var(--btn-active-text, #fff);
  }
</style>
