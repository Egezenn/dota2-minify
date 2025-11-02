import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if os.getcwd() != minify_root:
    os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)


import dearpygui.dearpygui as ui

import helper


def main():
    if not helper.workshop_installed:
        ui.configure_item(os.path.basename(current_dir), enabled=True)
