import os

import dearpygui.dearpygui as ui


def register_fonts():
    with ui.font_registry():
        with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 16, tag="main_font") as main_font:
            ui.add_font_range_hint(ui.mvFontRangeHint_Default)
            ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
            ui.add_font_range(0x0100, 0x017F)  # Turkish set
            ui.add_font_range(0x0370, 0x03FF)  # Greek set
            ui.bind_font(main_font)

        with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 14, tag="small_font"):
            ui.add_font_range_hint(ui.mvFontRangeHint_Default)
            ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
            ui.add_font_range(0x0100, 0x017F)  # Turkish set
            ui.add_font_range(0x0370, 0x03FF)  # Greek set

        with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 20, tag="large_font"):
            ui.add_font_range_hint(ui.mvFontRangeHint_Default)
            ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
            ui.add_font_range(0x0100, 0x017F)  # Turkish set
            ui.add_font_range(0x0370, 0x03FF)  # Greek set

        with ui.font(os.path.join("bin", "FiraMono-Medium.ttf"), 32, tag="very_large_font"):
            ui.add_font_range_hint(ui.mvFontRangeHint_Default)
            ui.add_font_range_hint(ui.mvFontRangeHint_Cyrillic)
            ui.add_font_range(0x0100, 0x017F)  # Turkish set
            ui.add_font_range(0x0370, 0x03FF)  # Greek set
