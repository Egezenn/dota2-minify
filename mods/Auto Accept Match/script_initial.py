import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if minify_root not in sys.path:
    sys.path.insert(0, minify_root)


import dearpygui.dearpygui as ui

import helper
import utils_gui


def main():
    if not helper.workshop_installed:
        for checkbox in utils_gui.checkboxes:
            if checkbox == os.path.basename(current_dir):
                ui.configure_item(checkbox, enabled=True)
                break
