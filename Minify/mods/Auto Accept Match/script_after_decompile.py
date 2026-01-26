import os
import sys
import xml.etree.ElementTree as ET

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

import helper
import mpaths


def main():
    if not helper.workshop_installed:
        return

    menu_xml_path = os.path.join(current_dir, "menu.xml")
    if not os.path.exists(menu_xml_path):
        return

    try:
        with open(menu_xml_path, encoding="utf-8") as file:
            menu_data = file.read()
            if not menu_data.strip().startswith(r"<Panel "):
                mpaths.write_warning(f"Improper mod menu on {os.path.basename(current_dir)}!")
                return
            menu_element = ET.fromstring(menu_data)
    except Exception as e:
        mpaths.write_warning(f"Failed to read/parse menu.xml: {e}")
        return

    minify_section_xml = r"""
<Panel class="SettingsSectionContainer" section="#minify" icon="s2r://panorama/images/control_icons/24px/check.vsvg">
  <Panel class="SettingsSectionTitleContainer LeftRightFlow">
    <Image class="SettingsSectionTitleIcon" texturewidth="48px" textureheight="48px" scaling="stretch-to-fit-preserve-aspect" src="s2r://panorama/images/control_icons/24px/check.vsvg" />
    <Label class="SettingsSectionTitle" text="Minify" />
  </Panel>
</Panel>
"""

    settings_path = os.path.join(
        mpaths.build_dir,
        "panorama",
        "layout",
        "popups",
        "popup_settings_reborn.xml",
    )

    if not os.path.exists(settings_path):
        mpaths.write_warning(f"Settings file not found at {settings_path}")
        return

    try:
        tree = ET.parse(settings_path)
        root = tree.getroot()
        settings_body = root.find(".//PopupSettingsRebornSettingsBody")

        if settings_body is not None:
            minify_section = ET.fromstring(minify_section_xml)
            settings_body.append(minify_section)
            minify_section.append(menu_element)
            tree.write(settings_path, encoding="utf-8")

    except ET.ParseError:
        mpaths.write_warning(f"Failed to parse {settings_path}")
    except Exception as e:
        mpaths.write_warning(f"Error applying menu mod: {e}")
