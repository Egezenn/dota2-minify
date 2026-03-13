import ctypes

import dearpygui.dearpygui as ui
from core import base


def theme():
    with ui.theme() as global_theme:
        with ui.theme_component(ui.mvAll):
            ui.add_theme_style(ui.mvStyleVar_WindowPadding, x=0, y=0)
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_WindowBg, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ChildBg, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarBg, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrab, (0, 200, 200))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrabHovered, (0, 170, 170))
            ui.add_theme_color(ui.mvThemeCol_ScrollbarGrabActive, (0, 120, 120))
            ui.add_theme_color(ui.mvThemeCol_TitleBg, (35, 35, 35, 255))
            ui.add_theme_color(ui.mvThemeCol_TitleBgActive, (35, 35, 35, 255))
            ui.add_theme_color(ui.mvThemeCol_Header, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_HeaderHovered, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_HeaderActive, (17, 17, 18, 255))
            ui.add_theme_style(ui.mvStyleVar_WindowBorderSize, 0)
            ui.add_theme_style(ui.mvStyleVar_ScrollbarRounding, 0)
    ui.bind_theme(global_theme)

    with ui.theme() as main_buttons_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Button, (0, 230, 230, 6))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (15, 15, 15, 255))
            ui.add_theme_style(ui.mvStyleVar_ButtonTextAlign, x=0, y=0.5)
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_Button, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (32, 32, 32, 255))
            ui.add_theme_style(ui.mvStyleVar_ButtonTextAlign, x=0, y=0.5)

    with ui.theme() as mod_menu_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (24, 24, 24, 255))
            ui.add_theme_color(ui.mvThemeCol_CheckMark, (0, 230, 230, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (20, 20, 20, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (20, 20, 20, 255))
        with ui.theme_component(ui.mvCheckbox, enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_CheckMark, (0, 70, 70, 255))
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (32, 32, 32, 255))
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Button, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (32, 32, 32, 255))

    with ui.theme() as footer_theme:
        with ui.theme_component():
            ui.add_theme_style(ui.mvStyleVar_WindowPadding, x=0, y=0)
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (32, 32, 32, 255))
        with ui.theme_component(enabled_state=False):
            ui.add_theme_color(ui.mvThemeCol_Button, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 100, 100))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (32, 32, 32, 255))
        with ui.theme_component(ui.mvCheckbox):
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (32, 32, 32, 255))

    with ui.theme() as popup_theme:
        with ui.theme_component():
            ui.add_theme_color(ui.mvThemeCol_Text, (0, 230, 230))
            ui.add_theme_color(ui.mvThemeCol_Button, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            ui.add_theme_color(ui.mvThemeCol_ButtonActive, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBg, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgHovered, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_FrameBgActive, (32, 32, 32, 255))
            ui.add_theme_color(ui.mvThemeCol_Border, (0, 230, 230, 150))
            ui.add_theme_color(ui.mvThemeCol_ModalWindowDimBg, (0, 0, 0, 200))
            ui.add_theme_style(ui.mvStyleVar_WindowBorderSize, 1)
            ui.add_theme_style(ui.mvStyleVar_WindowPadding, x=20, y=20)
            ui.add_theme_style(ui.mvStyleVar_ItemSpacing, x=10, y=10)

    ui.bind_item_theme("button_patch", main_buttons_theme)
    ui.bind_item_theme("button_select_mods", main_buttons_theme)
    ui.bind_item_theme("button_uninstall", main_buttons_theme)
    ui.bind_item_theme("mod_menu", mod_menu_theme)
    ui.bind_item_theme("footer", footer_theme)
    ui.bind_item_theme("modal_popup", popup_theme)


def enable_dark_titlebar(title):
    if base.OS == base.WIN:
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, title)
            if hwnd != 0:
                value = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except:
            pass
