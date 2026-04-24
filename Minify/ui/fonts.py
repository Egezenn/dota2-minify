"Font registrations with range hints"

import os

import dearpygui.dearpygui as dpg

# TODO: figure out how to use fonts with other locales, e.g Chinese, Korean etc. (Noto Sans maybe?)
#       Bundling the font in would result in a bigger size, need to make a cross-platform font loader
#       to use widely available fonts and load it from the system paths. Fallback to a download if
#       absolutely necessary (when that locale is selected).

# mvFontRangeHint_Default
# mvFontRangeHint_Japanese
# mvFontRangeHint_Korean
# mvFontRangeHint_Chinese_Full
# mvFontRangeHint_Chinese_Simplified_Common
# mvFontRangeHint_Cyrillic
# mvFontRangeHint_Thai
# mvFontRangeHint_Vietnamese


def register():
    with dpg.font_registry():
        with dpg.font(os.path.join("bin", "FiraMono-Medium.ttf"), 16, tag="main_font") as main_font:
            dpg.bind_font(main_font)

        with dpg.font(os.path.join("bin", "FiraMono-Medium.ttf"), 14, tag="small_font"):
            pass

        with dpg.font(os.path.join("bin", "FiraMono-Medium.ttf"), 20, tag="large_font"):
            pass

        with dpg.font(os.path.join("bin", "FiraMono-Medium.ttf"), 32, tag="very_large_font"):
            pass
