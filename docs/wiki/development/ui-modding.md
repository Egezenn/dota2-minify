## `styling.css`

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

### Dynamic Styling (Placeholders)

You can use settings defined in your `modcfg.json` directly within your `styling.css` using the `<&key>` syntax. These placeholders are replaced with the user-configured values during the patching process.

**Example**:
If you have a color picker in `modcfg.json`:

```json
{
  "key": "my_custom_color",
  "text": "Header Color",
  "default": "#00FF00FF",
  "type": "color"
}
```

You can use it in your `styling.css`:

```css
/* g:panorama/styles/main_styles */
.HeaderLabel {
  color: <&my_custom_color>;
}
```

## `xml_mod.json`

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

## Mod Settings & Custom Buttons

Mods can expose configurable settings to the user's **Settings Menu** via the `settings` array in `modcfg.json`.

### Custom Function Buttons

Besides standard inputs like checkboxes or color pickers, you can create a button that invokes a Python function from your mod's `script_utility.py`.

1. **Define the button in `modcfg.json`**:
   The `key` should match the name of the function you want to call.

   ```json
   {
     "key": "fetch_latest_data",
     "text": "Sync Hero Grids",
     "force": true,
     "type": "button",
   }
   ```

2. **Implement the function in `script_utility.py`**:

   ```python
   def fetch_latest_data():
       # Your custom logic here
       print("Fetching latest grids...")
   ```

When the user clicks the button in the Minify settings, `fetch_latest_data()` will be executed.
