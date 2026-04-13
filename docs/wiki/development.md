## Running from the source

Prerequisites are `git`, `python` and `uv`. (also `tk` for tkinter and `wine` for workshop tools executables on Linux)

```shell
git clone https://github.com/Egezenn/dota2-minify
cd dota2-minify
uv run Minify
```

## Creating mods

Minify has a programmatical approach to most modifications to keep everything minimal and simple. If there isn't a method available for your needs, you can always upload your mod files in `mods/<mod_name>/files` to be directly included into the pak minify is going to create or include a python script to accomodate specific behavior.

| Modifications to file                                                   | Restart required for changes | Workshop requirement |
| ----------------------------------------------------------------------- | ---------------------------- | -------------------- |
| [`files`](development/mod-structure.md#filesfiles_uncompiled-directory) | No                           | No<sup>1</sup>       |
| [`modcfg.json`](development/mod-structure.md#modcfgjson)                | Yes<sup>2</sup>              | -                    |
| [`notes.md`](development/mod-structure.md#notesmd)                      | Yes                          | -                    |
| `preview.png`                                                           | Yes                          | -                    |
| [`blacklist.txt`](development/mod-structure.md#blacklisttxt)            | No                           | No                   |
| [`replacer.csv`](development/mod-structure.md#replacercsv)              | No                           | No                   |
| [`script.py`](development/scripting.md#scriptpy)                        | No<sup>3</sup>               | No                   |
| [`styling.css`](development/ui-modding.md#stylingcss)                   | No                           | Yes                  |
| [`xml_mod.json`](development/ui-modding.md#xml_modjson)                 | No                           | Yes                  |

<sup>1</sup>: [Uncompiled files](development/mod-structure.md#filesfiles_uncompiled-directory).  
<sup>2</sup>: The build engine pulls `always` and `dependencies` dynamically each time a patch is started. However, keys that define the mod's presence or configuration in the UI (like `order`, `visual`, and `settings` structure) are only loaded during the initial scan; changing these requires clicking **Refresh** in the Settings menu or restarting the application to re-render the components.  
<sup>3</sup>: Initial scripts(`script_initial.py`).

### Mod files and explanations

For a detailed breakdown of modification types and how to use them, refer to the following sections:

- [Mod Structure](development/mod-structure.md)
- [Scripting](development/scripting.md)
- [UI Modding (Panorama)](development/ui-modding.md)

### Compilation

For instructions, refer to the [workflow](https://github.com/Egezenn/dota2-minify/blob/main/.github/workflows/release.yml).
