import ctypes

import dearpygui.dearpygui as dpg
from core import base


def theme():
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, x=0, y=0)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 230, 230))
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (0, 200, 200))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (0, 170, 170))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (0, 120, 120))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (35, 35, 35, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (35, 35, 35, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Header, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (17, 17, 18, 255))
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 0)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 0)
    dpg.bind_theme(global_theme)

    with dpg.theme() as main_buttons_theme:
        with dpg.theme_component():
            dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 230, 230, 6))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (15, 15, 15, 255))
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, x=0, y=0.5)
        with dpg.theme_component(enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 100, 100))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (32, 32, 32, 255))
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, x=0, y=0.5)

    with dpg.theme() as mod_menu_theme:
        with dpg.theme_component():
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (24, 24, 24, 255))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (0, 230, 230, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (20, 20, 20, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (20, 20, 20, 255))
        with dpg.theme_component(dpg.mvCheckbox, enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 100, 100))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (0, 70, 70, 255))
        with dpg.theme_component():
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 230, 230))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (32, 32, 32, 255))
        with dpg.theme_component(enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 100, 100))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (32, 32, 32, 255))

    with dpg.theme() as footer_theme:
        with dpg.theme_component():
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, x=0, y=0)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 230, 230))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (32, 32, 32, 255))
        with dpg.theme_component(enabled_state=False):
            dpg.add_theme_color(dpg.mvThemeCol_Button, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 100, 100))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (32, 32, 32, 255))
        with dpg.theme_component(dpg.mvCheckbox):
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (32, 32, 32, 255))

    with dpg.theme() as terminal_theme:
        with dpg.theme_component(dpg.mvChildWindow):
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, x=0, y=8)

    with dpg.theme() as popup_theme:
        with dpg.theme_component():
            dpg.add_theme_color(dpg.mvThemeCol_Text, (0, 230, 230))
            dpg.add_theme_color(dpg.mvThemeCol_Button, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (17, 17, 18, 255))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (32, 32, 32, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 230, 230, 150))
            dpg.add_theme_color(dpg.mvThemeCol_ModalWindowDimBg, (0, 0, 0, 200))
            dpg.add_theme_style(dpg.mvStyleVar_WindowBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, x=20, y=20)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, x=10, y=10)

    dpg.bind_item_theme("button_patch", main_buttons_theme)
    dpg.bind_item_theme("button_select_mods", main_buttons_theme)
    dpg.bind_item_theme("button_uninstall", main_buttons_theme)
    dpg.bind_item_theme("mod_menu", mod_menu_theme)
    dpg.bind_item_theme("footer", footer_theme)
    dpg.bind_item_theme("modal_popup", popup_theme)
    dpg.bind_item_theme("terminal_window", terminal_theme)


def enable_dark_titlebar(title):
    if base.OS == base.WIN:
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, title)
            if hwnd != 0:
                value = ctypes.c_int(1)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        except:
            pass
