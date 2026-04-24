"Dangling random functions"

import importlib.util
import os
import shutil
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import dearpygui.dearpygui as dpg
import vpk
from core import base, config, constants, fs, log, utils
from ui import terminal

compiler_filepicker_path = ""
output_path = config.get("output_path", constants.minify_default_dota_pak_output_path)


def get_blank_file_extensions():
    extensions = []
    for file in os.listdir(base.blank_files_dir):
        extensions.append(os.path.splitext(file)[1])
    return extensions


def change_output_path():
    global output_path
    selection = dpg.get_value("output_select")
    output_path = [lang for lang in constants.minify_dota_possible_language_output_paths if selection in lang][0]
    config.set("output_locale", selection)
    config.set("output_path", output_path)


def compile():
    """
    A wrapper for the Dota 2 Resource Compiler.
    """
    with open(base.log_rescomp, "wb") as file:
        command = [
            constants.dota_resource_compiler_path,
            "-i",
            constants.minify_dota_compile_input_path + "/*",
            "-r",
        ]

        if base.OS != base.WIN:
            command.insert(0, "wine")

        rescomp = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,  # compiler complains if minify_dota_compile_input_path is empty
            creationflags=subprocess.CREATE_NO_WINDOW if base.OS == base.WIN else 0,
        )
        if rescomp.stdout != b"":
            file.write(rescomp.stdout)


def compile_assets(input_path=None, output_path=None, pak_path=None, sender=None, app_data=None, user_data=None):
    """
    resourcecompiler's friendly cousin
    Automagically handles image compilation
    """
    if compiler_filepicker_path:
        input_path = compiler_filepicker_path
        output_path = os.path.join(input_path, os.pardir, "#Minify_compiled")
        terminal.clean()
    if not output_path:
        output_path = os.path.join(input_path, os.pardir, "#Minify_compiled")

    img_list = [str(f.relative_to(input_path)) for f in Path(input_path).rglob("*.png") if f.is_file()]

    if os.path.exists(input_path):
        terminal.add_text("&compile_init", input_path)
        fs.remove_path(constants.minify_dota_compile_input_path, output_path)
        fs.create_dirs(constants.minify_dota_compile_input_path)

        with utils.open_utf8(os.path.join(input_path, "ref.xml"), "w") as file:
            file.write(create_img_ref_xml(img_list))

        items = os.listdir(input_path)

        for item in items:
            if os.path.isdir(os.path.join(input_path, item)):
                shutil.copytree(
                    os.path.join(input_path, item),
                    os.path.join(constants.minify_dota_compile_input_path, item),
                )
            else:
                shutil.copy(os.path.join(input_path, item), constants.minify_dota_compile_input_path)

        compile()

        fs.create_dirs(constants.minify_dota_compile_output_path)
        shutil.copytree(os.path.join(constants.minify_dota_compile_output_path), output_path)

        fs.remove_path(
            constants.minify_dota_compile_input_path,
            constants.minify_dota_compile_output_path,
            os.path.join(input_path, "ref.xml"),
            os.path.join(output_path, "ref.vxml_c"),
        )
        fs.create_dirs(constants.minify_dota_tools_required_path)

        terminal.add_text("&compile_successful", output_path)

        if pak_path:
            vpk_file = vpk.new(output_path)
            vpk_file.save(pak_path)
            terminal.add_text("&compile_created_pak", pak_path)
    else:
        terminal.add_text("&compile_no_path")


def create_img_ref_xml(img_path_list):
    "Helper function to create reference XMLs for images"
    xml_list = []
    for img_path in img_path_list:
        xml_list.append(f'\t\t\t<Image src="file://{img_path}" />')

    return rf"""<root>
    <Panel class="AddonLoadingRoot">
{"\n".join(xml_list)}
    </Panel>
</root>
"""


def select_compile_dir(sender=None, app_data=None):
    global compiler_filepicker_path
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askdirectory(initialdir=os.getcwd())
    root.destroy()
    if path:
        compiler_filepicker_path = path


def exec_script(script_path, mod_name, order_name, _terminal_output=True):
    """
    Injects code
    Only called for `script.py`
    """
    if os.path.exists(script_path):
        script_dir = os.path.dirname(script_path)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        module_name = mod_name.replace(" ", "").lower() + f"_{order_name}_script"
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        main_func = getattr(module, "main", None)
        if callable(main_func):
            if _terminal_output:
                terminal.add_text("&script_execution", mod_name, order_name)
            main_func()
            if _terminal_output:
                terminal.add_text("&script_success", mod_name, order_name, msg_type="success")
        else:
            log.write_warning("&script_no_main", mod_name, order_name)


def bulk_exec_script(order_name, terminal_output=True):
    """
    Injects required mod instructions in bulk

    `script_initial.py`
    `script_after_decompile.py`
    `script_after_recompile.py`
    `script_after_patch.py`
    `script_uninstall.py`
    """
    bulk_name = f"script_{order_name}.py"
    for root, _, files in os.walk(base.mods_dir):
        if bulk_name in files and not os.path.basename(root).startswith("_"):
            mod_cfg_path = os.path.join(root, "modcfg.json")
            cfg = config.read_json_file(mod_cfg_path)
            always = cfg.get("always", False)
            visual = cfg.get("visual", True)

            # TODO: pull the file from pak66 to check if it was enabled for uninstallers
            if always or order_name in ["initial", "uninstall"] or (visual and dpg.get_value(os.path.basename(root))):
                exec_script(
                    os.path.join(root, bulk_name), os.path.basename(root), order_name, _terminal_output=terminal_output
                )


def exec_script_function(script_path, mod_name, function_name="main"):
    """
    Executes a specific function from a Python script file
    """
    if os.path.exists(script_path):
        script_dir = os.path.dirname(script_path)
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)

        module_name = mod_name.replace(" ", "").lower() + "_utility"
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        func = getattr(module, function_name, None)
        if callable(func):
            func()
        else:
            log.write_warning(f"Function '{function_name}' not found in {script_path}")
    else:
        log.write_warning(f"Script file not found: {script_path}")
