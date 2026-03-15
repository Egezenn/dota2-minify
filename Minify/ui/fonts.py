import os

import dearpygui.dearpygui as dpg


def register():
    with dpg.font_registry():
        with dpg.font(os.path.join("bin", "FiraMono-Medium.ttf"), 16, tag="main_font") as main_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            dpg.add_font_range(0x0100, 0x017F)  # Turkish set
            dpg.add_font_range(0x0370, 0x03FF)  # Greek set
            dpg.bind_font(main_font)

        with dpg.font(os.path.join("bin", "FiraMono-Medium.ttf"), 14, tag="small_font"):
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            dpg.add_font_range(0x0100, 0x017F)  # Turkish set
            dpg.add_font_range(0x0370, 0x03FF)  # Greek set

        with dpg.font(os.path.join("bin", "FiraMono-Medium.ttf"), 20, tag="large_font"):
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            dpg.add_font_range(0x0100, 0x017F)  # Turkish set
            dpg.add_font_range(0x0370, 0x03FF)  # Greek set

        with dpg.font(os.path.join("bin", "FiraMono-Medium.ttf"), 32, tag="very_large_font"):
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            dpg.add_font_range(0x0100, 0x017F)  # Turkish set
            dpg.add_font_range(0x0370, 0x03FF)  # Greek set
