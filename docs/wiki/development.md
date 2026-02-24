## Running from the source

Prerequisites are `git`, `python` and `uv`. (also `tk` for tkinter and `wine` for workshop tools executables)

```shell
git clone https://github.com/Egezenn/dota2-minify
cd dota2-minify
uv run Minify
```

## Creating mods

Minify has a programmatical approach to most modifications to keep everything minimal and simple. If there isn't a method available for your needs, you can always upload your mod files in `mods/<mod_name>/files` to be directly included into the pak minify is going to create or include a python script to accomodate specific behavior.

| Modifications to file                       | Restart required for changes | Workshop requirement |
| ------------------------------------------- | ---------------------------- | -------------------- |
| [`files`](#filesfiles_uncompiled-directory) | No                           | No<sup>1</sup>       |
| [`modcfg.json`](#modcfgjson)                | Yes<sup>2</sup>              | -                    |
| [`notes.md`](#notesmd)                      | Yes                          | -                    |
| `preview.png`                               | Yes                          | -                    |
| [`blacklist.txt`](#blacklisttxt)            | No                           | No                   |
| [`replacer.csv`](#replacercsv)              | No                           | No                   |
| [`script.py`](#scriptpy)                    | No<sup>3</sup>               | No                   |
| [`styling.css`](#stylingcss)                | No                           | Yes                  |
| [`xml_mod.json`](#xml_modjson)              | No                           | Yes                  |

<sup>1</sup>: [Uncompiled files](#filesfiles_uncompiled-directory).  
<sup>2</sup>: The keys `always` and `dependencies` will be pulled at patch time, others require reinitialization.  
<sup>3</sup>: Initial scripts(`script_initial.py`).

### Mod files and explanations

```plaintext
mods
├── <mod_name>
│   ├── files
│   │   ├── <path_to_file_in_pak>
│   │   ├── <...>
│   │   └── <...>
│   ├── files_uncompiled
│   │   ├── <path_to_file_in_pak>
│   │   ├── <...>
│   │   └── <...>
│   ├── modcfg.json
│   ├── notes.md
│   ├── preview.png
│   ├── blacklist.txt
│   ├── replacer.csv
│   ├── script.py
│   ├── script_initial.py
│   ├── script_after_decompile.py
│   ├── script_after_recompile.py
│   ├── script_after_patch.py
│   ├── script_uninstall.py
│   ├── styling.css
│   └── xml_mod.json
```

#### `modcfg.json`

```json
{ // defaults doesn't need to be indicated
  "always": false, // false by default, apply them without checking mods.json or checkbox
  "dependencies": ["<mod>"], // None by default, add a mod dependency's name here 
  "order": 1, // default is 1, ordered from negative to positive to resolve any conflicts
  "visual": true // true by default, show it in the UI as a checkbox
}
```

#### `files`|`files_uncompiled` directory

`files` directory will drop the files put here into the pak that minify is going to create. These files should already be compiled.

`files_uncompiled` will drop the files onto the input folder **if the workshop tools are available**.

If not specifically protected by Dota2, these files will override any game content. This also applies for the rest of the modification methods available.

#### `notes.md`

Displays information about a mod on `Details` window.

An image is rendered at the top if the file `preview.png` exists.

```markdown
<!-- LANG:EN -->
Normal text supports `inline code` (pink) and https://example.com (orange).

- This is a list item.
- List items support `inline code` too.
- And they support https://example.com as well.

!!: This is an emphasized warning (Red & Large).
!!: It supports `pink code` blocks.
!!: And https://example.com links.
```

![notes](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/example-notes.png)

#### `blacklist.txt`

This file is a list of path to files used to override those with blanks.
Supported file types can be found in [`bin/blank-files`](https://github.com/Egezenn/dota2-minify/tree/main/Minify/bin/blank-files).

A list of all the files (from the game pak) can be found in `bin/gamepakcontents.txt` of your installation.

| Modifier | Value               | Purpose                          |
| -------- | ------------------- | -------------------------------- |
|          | `path/to/file`      | Blacklisting a single file       |
| `>>`     | `path/to/directory` | Blacklisting an entire directory |
| `--`     | `path/to/file`      | Exclusion                        |
| `**`     | RegExp pattern      | Blacklisting patterns            |
| `*-`     | RegExp pattern      | Excluding patterns               |
| `#`      | Comment             |                                  |

After that with no blank spaces you put the path to the file you want to override.
`path/to/file`

```plaintext
particles/base_attacks/ranged_goodguy_launch.vpcf_c
>>particles/sprays
**taunt.*\.vsnd_c
```

#### `replacer.csv`

This file allows you to replace file(s) with other file(s) inside the game VPK (can be used for skin swappers etc.).

Format:  
`file_to_be_replaced,replacement_file`

Example:

```csv
panorama/images/spellicons/nevermore_shadowraze1_png.vtex_c,panorama/images/spellicons/nevermore_shadowraze1_demon_png.vtex_c
panorama/images/spellicons/nevermore_shadowraze2_png.vtex_c,panorama/images/spellicons/nevermore_shadowraze2_demon_png.vtex_c
panorama/images/spellicons/nevermore_shadowraze3_png.vtex_c,panorama/images/spellicons/nevermore_shadowraze3_demon_png.vtex_c
```

![example-replacer](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/example-replacer.png)

#### `script.py`

If and when there is a specific behavior to be automated you can include a python script along with your mod. You can find the template below.

Appending `_initial, _after_decompile, _after_recompile, _uninstall` to your script's name will adjust when it'll be executed. Thus giving you the full control of how your mod can be handled. By default it executes while iterating over each mod when you are patching.

```python
# This script template can be run both manually and from minify.
# You are able to use packages and modules from minify (you need an activated environment from the minify root or running with the tool `uv` can automatically handle this.)
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# Any package or module native to minify can be imported here
# import requests
#
# import mpaths
# ...


def main():
    pass
    # Code specific to your mod goes here, minify will try to execute this block.
    # If any exceptions occur, it'll be written to `logs` directory


if __name__ == "__main__":
    main()
```

#### `styling.css`

This file is a list of VCSS paths and styling that will be appended to them.  
By the nature of this method modifications done here may break the original XML or CSS that gets updated resulting in a bad layout.  
In such cases, a repatch or a slight modification is required.

If you encounter errors while patching, it's most likely that your CSS is invalid or the path is wrong. Check [`logs/resourcecompiler.txt`](Minify/logs/resourcecompiler.txt) for more information.

For Source 2 flavored CSS properties, refer to: [Valve Developer Community Wiki](https://developer.valvesoftware.com/wiki/Dota_2_Workshop_Tools/Panorama/CSS_Properties).  
To live inspect the layout, open the workshop tools and press <kbd>F6</kbd> and select the element you'd like to select from the XML.

Syntax:

```css
/* g|c:path/to/vcss_file_without_extension */
example_selector { property: value; }
/* it can also override definitions */
@define foo: bar;
@keyframes 'anim-name'
{
  progress
  {
    property: value;
  }
}
```

#### `xml_mod.json`

This file allows you to modify Valve's XML (Panorama) files dynamically. It uses a key-value structure where the key is the path to the XML file in the VPK (e.g., `panorama/layout/popups/popup_accept_match.xml`) and the value is a list of modification actions.

Example:

```json
{
  "panorama/layout/popups/popup_accept_match.xml": [
    {
      "action": "add_script",
      "src": "s2r://panorama/scripts/popups/popup_auto_accept_match.vjs_c"
    },
    {
      "action": "set_attribute",
      "tag": "PopupAcceptMatch",
      "attribute": "onload",
      "value": "AcceptMatchPopup()"
    }
  ]
}
```

Supported actions:

| `add_script` | Adds a script include to the `<scripts>` section.                                        |
| :----------- | :--------------------------------------------------------------------------------------- |
| `src`        | Path to the script (e.g., `s2r://panorama/scripts/popups/popup_auto_accept_match.vjs_c`) |

| `add_style_include` | Adds a style include to the `<styles>` section.                                    |
| :------------------ | :--------------------------------------------------------------------------------- |
| `src`               | Path to the style (e.g., `s2r://panorama/styles/popups/popup_accept_match.vcss_c`) |

| `set_attribute` | Sets an attribute on an element.   |
| :-------------- | :--------------------------------- |
| `tag`           | The tag name or ID of the element. |
| `attribute`     | Name of the attribute to set.      |
| `value`         | Value of the attribute.            |

| `add_child` | Appends a child element to a parent. |
| :---------- | :----------------------------------- |
| `parent_id` | ID of the parent element.            |
| `xml`       | The XML string of the child element. |

| `move_into`     | Moves an element into a new parent. |
| :-------------- | :---------------------------------- |
| `target_id`     | ID of the element to move.          |
| `new_parent_id` | ID of the new parent element.       |

| `insert_after` | Inserts an element after a target element. |
| :------------- | :----------------------------------------- |
| `target_id`    | ID of the reference element.               |
| `xml`          | The XML string to insert.                  |

| `insert_before` | Inserts an element before a target element. |
| :-------------- | :------------------------------------------ |
| `target_id`     | ID of the reference element.                |
| `xml`           | The XML string to insert.                   |

### Compilation

For instructions, refer to the [workflow](https://github.com/Egezenn/dota2-minify/blob/main/.github/workflows/release.yml).
