import { build } from "vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { sveltePreprocess } from "svelte-preprocess";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runBuild() {
  const noPlugins = process.argv.includes("--no-plugins");
  console.log(`Building main Web UI${noPlugins ? " (no plugins)" : ""}...`);

  const mainOutDir = path.resolve(__dirname, "../dist");

  // 1. Build main application to Minify/ui/dist
  await build({
    configFile: path.resolve(__dirname, "vite.config.js"),
    base: "./",
    root: __dirname,
    build: {
      outDir: mainOutDir,
      emptyOutDir: true,
      rollupOptions: {
        input: {
          main: path.resolve(__dirname, "index.html"),
        },
      },
    },
  });

  const pluginsDir = path.resolve(__dirname, "../../plugins");

  // If --no-plugins is specified, remove ui directory in all plugins and return
  if (noPlugins) {
    if (fs.existsSync(pluginsDir)) {
      const pluginFolders = fs.readdirSync(pluginsDir);
      for (const folder of pluginFolders) {
        if (folder.startsWith(".") || folder.startsWith("_")) continue;
        const pluginUiDir = path.resolve(pluginsDir, folder, "ui");
        if (fs.existsSync(pluginUiDir)) {
          fs.rmSync(pluginUiDir, { recursive: true, force: true });
        }
      }
    }
    console.log("Build completed successfully (core only, no plugins).");
    return;
  }

  // 2. Discover and build plugin Svelte+TS entry points into plugins/<folder>/ui
  const stagingParent = path.resolve(__dirname, ".staging");

  if (fs.existsSync(pluginsDir)) {
    const pluginFolders = fs.readdirSync(pluginsDir);
    for (const folder of pluginFolders) {
      if (folder.startsWith(".") || folder.startsWith("_")) continue;
      const pluginSrcDir = path.resolve(pluginsDir, folder, "src");
      const pluginHtml = path.resolve(pluginSrcDir, "index.html");

      if (fs.existsSync(pluginHtml)) {
        console.log(`Building Svelte+TS plugin: ${folder}...`);

        const stagingDir = path.resolve(stagingParent, folder);
        fs.mkdirSync(stagingDir, { recursive: true });
        fs.cpSync(pluginSrcDir, stagingDir, { recursive: true });

        const stagedHtml = path.resolve(stagingDir, "index.html");
        const pluginOutDir = path.resolve(pluginsDir, folder, "ui");

        await build({
          configFile: false,
          plugins: [svelte({ preprocess: sveltePreprocess() })],
          base: "./",
          root: stagingDir,
          build: {
            outDir: pluginOutDir,
            emptyOutDir: true,
            rollupOptions: {
              input: {
                index: stagedHtml,
              },
            },
          },
        });

        fs.rmSync(stagingDir, { recursive: true, force: true });
      }
    }

    if (fs.existsSync(stagingParent)) {
      fs.rmSync(stagingParent, { recursive: true, force: true });
    }
  }

  console.log("Build completed successfully.");
}

runBuild().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
