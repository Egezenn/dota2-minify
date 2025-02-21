#  __    __     __     __   __     __     ______   __  __    
# /\ "-./  \   /\ \   /\ "-.\ \   /\ \   /\  ___\ /\ \_\ \   
# \ \ \-./\ \  \ \ \  \ \ \-.  \  \ \ \  \ \  __\ \ \____ \  
#  \ \_\ \ \_\  \ \_\  \ \_/"\_\  \ \_\  \ \_\    \/\_____\ 
#   \/_/  \/_/   \/_/   \/_/ \/_/   \/_/   \/_/     \/_____/ 
# ---------------------------------------------------------- 

# this code was written when I was newer to programming and not worth the headache to try to improve.
# instead if you want to help develop contact me on discord and help work on Minify 2.0 -- a full stack desktop app.
# https://github.com/robbyz512/dota2-minify?tab=readme-ov-file#fast_forward-future-of-this-project---minify-20
# discord = robbyz

import os
import sys
import requests
import vpk
import shutil
import psutil
import traceback
import filecmp
import threading
import subprocess
import tkinter as tk
from tkinter.messagebox import askyesno
from functools import partial
from shutil import copytree, ignore_patterns
from PIL import Image, ImageTk

import mpaths
import validatefiles
import helper

version = "1.07"

# widget vars
btnXpad = 8
btnYpad = 8
btnW = 8

patching = False
checkboxes = {}
blacklist_dictionary = {}
styling_dictionary = {}

def welcomeMsg():
    print(r""" __    __     __     __   __     __     ______   __  __    
 /\ "-./  \   /\ \   /\ "-.\ \   /\ \   /\  ___\ /\ \_\ \   
 \ \ \-./\ \  \ \ \  \ \ \-.  \  \ \ \  \ \  __\ \ \____ \  
  \ \_\ \ \_\  \ \_\  \ \_/"\_\   \ \_\  \ \_\    \/\_____\ 
   \/_/  \/_/   \/_/   \/_/ \/_/   \/_/   \/_/     \/_____/ 
 -------------------------------------------------------  
 Want to contribute to the project's growth?
       
 -> Join our Discord community ♥
 -> Share Minify with your friends and online groups
 -> Star the project on GitHub ★
 -> Contribute to the development of Minify 2.0
 -> Create mods for this project
 -------------------------------------------------------
       """)

def failureMsg():
    print(r""":( Failed to connect to 
https://github.com/robbyz512/dota2-minify-remote/tree/remote-data
          
Either you are not connected to the internet or your network configuration is not allowing this app to make requests to Github
          
Minify may not work correctly.
-------------------------------------------------------
    """)

class Extension:
    def __init__(self, path):
        self.path = path
        self.css = path + '.css'
        self.vcss_c = path + '.vcss_c'
        self.xml = path + '.xml'
        self.vxml_C = path + '.vxml_c'

class Path:
    def __init__(self, path, style):
        self.path = Extension(path)
        self.style = style

class TextRedirector(object):
    def __init__(self, widget, tag="stdout"):
        self.widget = widget
        self.tag = tag

    def write(self, str):
        self.widget.configure(state="normal") 
        self.widget.insert("end", " " + str, (self.tag))
        self.widget.see('end')
        self.widget.configure(state="disabled")

class App():
    def __init__(self):
        self.root = tk.Tk()
        self.root.protocol('WM_DELETE_WINDOW', self.exit)
        self.setupGUI()
        self.setupSystem()
        self.setupButtonState()
        self.root.mainloop()

    def exit(self):
        self.root.destroy()
    
    def restart_app(self):
        self.root.destroy()

    def setupGUI(self):
        # ------------------------------ gui properties ------------------------------ #
        self.root.title("Minify Dota2")
        self.root.iconbitmap('bin/images/favicon.ico')
        self.root.resizable(False, False)
        self.app_width = 800
        self.app_height = helper.getAppHeight(mpaths.mods_folders)
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        self.x = (self.screen_width / 2) - (self.app_width / 2)
        self.y = (self.screen_height / 2) - (self.app_height / 2)
        self.root.geometry(f'{self.app_width}x{self.app_height}+{int(self.x)}+{int(self.y)}')
        # -------------------------------- widgets -------------------------------- #

        self.checkboxesFrame = tk.Frame(self.root)
        self.checkboxesFrame.grid(row=0, column=0, padx=btnXpad, sticky='w')

        self.buttonsFrame = tk.Frame(self.root)
        self.buttonsFrame.grid(row=1, column=0, pady=13, sticky='nsew')
        
        self.consoleFrame = tk.Frame(self.root)
        self.consoleFrame.grid(row=0, column=1, rowspan=2, pady=5, padx=5, sticky='nsew')

        # Checkboxes
        def change_color_to_red(event):
            event.widget.config(fg="#0cb6b3")

        def revert_color(event):
            event.widget.config(fg="#333333")  # Original color when the cursor is not hovering

        for index in range(len(mpaths.mods_folders)):
            self.name = mpaths.mods_folders[index]
            self.current_var = tk.IntVar()
            self.current_box = tk.Checkbutton(self.checkboxesFrame, text=self.name, variable=self.current_var, takefocus=False, cursor="hand2", command=self.setupButtonState)
            self.current_box.var = self.current_var
            self.current_box.grid(row=index, column=0, sticky='w')
            checkboxes[self.current_box] = self.name  # so checkbutton object is the key and value is string
            
            # Bind mouse enter and leave events to change the text color
            self.current_box.bind("<Enter>", change_color_to_red)
            self.current_box.bind("<Leave>", revert_color)
            
            # details label
            mod_path = os.path.join(mpaths.mods_dir, self.name)
            notes_txt = os.path.join(mod_path, 'notes.txt')
            if os.path.exists(notes_txt) and os.stat(notes_txt).st_size != 0:
                self.modLabel = tk.Label(self.checkboxesFrame, font=("Poplar Std", 7), fg="#0000EE", cursor="hand2")
                self.modLabel.config(text="details")
                self.modLabel.bind("<Enter>", partial(helper.modLabelColorConfig, self.modLabel, "#000010"))
                self.modLabel.bind("<Leave>", partial(helper.modLabelColorConfig, self.modLabel, "#0000EE"))
                self.modLabel.bind("<Button-1>", partial(helper.modInfo, self.modLabel, self.name, mod_path))
                self.modLabel.grid(row=index, column=1, sticky='w')

        # Buttons
        self.patchBtn = tk.Button(self.buttonsFrame, text='Patch', state=tk.NORMAL, width=btnW, takefocus=False, command=lambda:threading.Thread(target=self.patcher, daemon=True).start())
        self.patchBtn.grid(row=10, column=0, pady=btnYpad, padx=btnXpad, sticky='w')
        self.helpBtn = tk.Button(self.buttonsFrame, text='Help', state=tk.NORMAL, width=btnW, takefocus=False, cursor="hand2", command=lambda:threading.Thread(target=helper.urlDispatcher(helper.help_url), daemon=True).start())
        self.helpBtn.grid(row=10, column=1, pady=btnYpad, padx=btnXpad, sticky='w')
        self.updateBtn = tk.Button(self.buttonsFrame, text='Update', state=tk.NORMAL, width=btnW, takefocus=False, command=lambda:threading.Thread(target=helper.urlDispatcher(helper.update_url), daemon=True).start())
        self.updateBtn.grid(row=11, column=0, pady=btnYpad, padx=btnXpad, sticky='w')
        self.uninstallBtn = tk.Button(self.buttonsFrame, text='Uninstall', width=btnW, takefocus=False, cursor="hand2", command=lambda:threading.Thread(target=self.uninstaller, daemon=True).start())
        self.uninstallBtn.grid(row=11, column=1, pady=btnYpad, padx=btnXpad, sticky='w')
        self.versionLabel = tk.Label(self.buttonsFrame, font=("None", 8), width=20)
        self.versionLabel.grid(row=12, column=0, sticky='w')
        self.discordBtn = tk.Button(self.buttonsFrame, text='Discord', width=btnW, takefocus=False, cursor="hand2", command=lambda:threading.Thread(target=helper.urlDispatcher(helper.discord_url), daemon=True).start())
        self.discordBtn.grid(row=14, column=0, pady=btnYpad, padx=btnXpad, sticky='w')
        self.exitBtn = tk.Button(self.buttonsFrame, text='Exit', width=btnW, takefocus=False, cursor="hand2", command=self.exit)
        self.exitBtn.grid(row=14, column=1, pady=btnYpad, padx=btnXpad, sticky='w')

        # Other Widget
        self.consoleText = tk.Text(self.consoleFrame, wrap=tk.WORD, state=tk.DISABLED, width=65, borderwidth=2, bg="#FFFFF7", relief="groove")
        self.consoleText.grid(row=0,column=0)
        self.consoleText.configure(font=("Fixedsys"))

        self.devLabel = tk.Label(self.consoleFrame, font=("Tahoma", 10))
        self.devLabel.config(text="Minify 2.0 under development")
        self.devLabel.grid(row=1, column=0, pady=4, sticky='s')
        self.devbtn = tk.Button(self.consoleFrame, text='Preview', width=22, cursor="hand2", height=1, font=("None", 8, "bold"), takefocus=False, command=lambda:threading.Thread(target=helper.urlDispatcher(helper.new_version), daemon=True).start())
        self.devbtn.grid(row=1, column=0, pady=4, sticky='e')

        self.donateLabel = tk.Label(self.consoleFrame, font=("Tahoma", 10), fg="#333333", bg="white")
        self.donateLabel.config(text="If you'd like to say thanks you can send a donation below.\nHelps me stay motivated to keep this project updated and develop it further.")
        self.donateLabel.grid(row=2, column=0, pady=50, sticky='s')

        self.donate_image = Image.open("bin/images/coffee.jpg")
        self.donate_photo = ImageTk.PhotoImage(self.donate_image)
        self.donateBtn = tk.Button(self.consoleFrame, image=self.donate_photo, width=155, height=28, cursor="hand2", takefocus=False, command=lambda:threading.Thread(target=helper.urlDispatcher(helper.donations_url), daemon=True).start())
        self.donateBtn.grid(row=2, column=0, pady=0, sticky='s')
        
        self.donate_image2 = Image.open("bin/images/crypto.jpg")
        self.donate_photo2 = ImageTk.PhotoImage(self.donate_image2)
        self.donateBtn2 = tk.Button(self.consoleFrame, image=self.donate_photo2, width=155, height=28, cursor="hand2", takefocus=False,  command=lambda: threading.Thread(target=helper.cryptoInfo, daemon=True).start())
        self.donateBtn2.grid(row=3, column=0, pady=10, sticky='s')
        
        # redirects stdout and stderror to text box widget, which means print statements will not appear in the gui until these two lines are ran
        sys.stdout = TextRedirector(self.consoleText, "stdout")
        sys.stderr = TextRedirector(self.consoleText, "stderr")

        if helper.response.status_code == 200:
            welcomeMsg()
        else:
            failureMsg()

        if helper.latest_version_url == None:
            pass
        else:
            if version == helper.latest_version_url:
                self.updateBtn.config(state='disabled', cursor="")
                self.versionLabel.config(fg="#0cb6b3", text=f"Latest version: {version}")
            else:
                self.updateBtn.config(state='normal', fg='blue', cursor="hand2")
                self.versionLabel.config(fg="blue", text=f"Update available: {helper.latest_version_url}")

                answer = askyesno(title='Update', message='New version available. Go to Download page now?')
                if answer:
                   helper.urlDispatcher(helper.update_url)
                else:
                    pass

    def setupSystem(self):
        x = validatefiles.MyClass(checkboxes, self.root)
        public_methods = [method for method in dir(x) if callable(getattr(x, method)) if not method.startswith('_')]  # private methods start with _
        try:
            for method in public_methods:
                getattr(x, method)()
                if x.toggle_flag == True:
                    helper.toggleFrameOff(self.checkboxesFrame, self.buttonsFrame)
                    break
        except Exception:
            with open(os.path.join(mpaths.logs_dir, 'crashlog.txt'), 'w') as file:
                file.write(traceback.format_exc())
                helper.toggleFrameOff(self.checkboxesFrame, self.buttonsFrame)
                print("Failed to start!")
                print("Check 'logs\\crashlog.txt' for more info.")

    def setupButtonState(self):  
        for box in checkboxes:
            if box.var.get() == 1:
                self.patchBtn.config(state='normal', cursor="hand2")
                break
            else:
                self.patchBtn.config(state='disabled', cursor="")

        if helper.workshop_installed == False:
            helper.disableWorkshopMods(mpaths.mods_dir, mpaths.mods_folders, checkboxes)

    def uninstaller(self):
        answer = askyesno(title='Confirm', message='Remove all mods?')
        if answer:

            # remove pak01_dir.vpk if it exists
            vpkPath = os.path.join(mpaths.dota_minify, 'pak01_dir.vpk')
            if os.path.exists(vpkPath): os.remove(vpkPath)

            # remove dota.vpk if it exists
            mapPath = os.path.join(mpaths.dota_minify_maps, 'dota.vpk')
            if os.path.exists(mapPath): os.remove(mapPath)

            # default builds will be reinstalled if they don't exist in the path
            with open(os.path.join(mpaths.itembuilds_dir, "default_antimage.txt"), 'r') as file:
                lines = file.readlines()
            if len(lines) >= 3:
                if "OpenDotaGuides" in lines[2]:
                    for file in os.listdir(mpaths.itembuilds_dir):
                        os.remove(file)

            print("All Minify mods have been removed.")
    # ---------------------------------------------------------------------------- #
    #                                     Main                                     #
    # ---------------------------------------------------------------------------- #
    def patcher(self):
        global patching
        
        if "dota2.exe" in (p.name() for p in psutil.process_iter()):
            print("Please close Dota 2 first and then patch.")
            return

        patching = True 
        helper.toggleFrameOff(self.checkboxesFrame, self.buttonsFrame)

        try: 
            # clean up previous patching data
            helper.cleanFolders(mpaths.build_dir, mpaths.logs_dir, mpaths.content_dir, mpaths.game_dir, mpaths.minify_dir, mpaths.dota_minify_maps)

            styling_dictionary = {}
            # blacklist_dictionary = {}
            helper.warnings = []

            blank_file_extensions = helper.getBlankFileExtensions(mpaths.blank_files_dir) # list of extensions in bin/blank-files
            blacklist_data = [] # path from every blacklist.txt
            styling_data = [] # path and style from every styling.txt

            for folder in mpaths.mods_folders:
                try:
                    mod_path = os.path.join(mpaths.mods_dir, folder)
                    # files_total = sum([len(files) for r, d, files in os.walk(os.path.join(mod_path, 'files'))])
                    blacklist_txt = os.path.join(mod_path, 'blacklist.txt')
                    styling_txt = os.path.join(mod_path, 'styling.txt') 

                    for box in checkboxes:
                        if box.var.get() == 1 and checkboxes[box] == folder: # step into folders that have ticked checkboxes only
                            print("→ Installing " + folder)
                            
                            if checkboxes[box] == 'Dark Terrain' or checkboxes[box] == 'Remove Foilage':
                                shutil.copytree(mpaths.maps_dir, os.path.join(mpaths.dota_minify, os.path.basename(mpaths.maps_dir)), dirs_exist_ok=True)
                            if checkboxes[box] == 'OpenDotaGuides Guides':
                                zip_path = os.path.join(mod_path, 'files', 'OpenDotaGuides.zip')
                                temp_dump_path = os.path.join(mod_path, 'files', 'temp')
                                if os.path.exists(zip_path):
                                    os.remove(zip_path)
                                response = requests.get('https://github.com/Egezenn/OpenDotaGuides/releases/latest/download/itembuilds.zip')
                                if response.status_code == 200:
                                    with open(zip_path, 'wb') as file:
                                        file.write(response.content)
                                    print('→ Downloaded latest OpenDotaGuides guides.')
                                    shutil.unpack_archive(zip_path, temp_dump_path, 'zip')
                                    for file in os.listdir(temp_dump_path):
                                        shutil.copy(os.path.join(temp_dump_path, file), os.path.join(mpaths.itembuilds_dir, file))
                                    shutil.rmtree(temp_dump_path)
                                    os.remove(zip_path)
                                    print('→ Replaced default guides with OpenDotaGuides guides.')
                                else:
                                    print('→ Failed to download latest OpenDotaGuides guides.')
                            # ----------------------------------- files ---------------------------------- #
                            # if files_total == 0:    pass
                            # elif files_total == 1:  print(f"    files: Found {files_total} file")
                            # else:                   print(f"    files: Found {files_total} files")
                            shutil.copytree(os.path.join(mod_path, 'files'), mpaths.game_dir, dirs_exist_ok=True, ignore=ignore_patterns('*.gitkeep'))
                            # ------------------------------- blacklist.txt ------------------------------ #
                            if os.stat(blacklist_txt).st_size == 0: pass
                            else:
                                with open(blacklist_txt) as file:

                                    lines = file.readlines()

                                    for index, line in enumerate(lines):
                                        line = line.strip()

                                        if line.startswith('#') or line.isspace():
                                            continue

                                        elif line.startswith('@@'):
                                            for path in helper.processBlackList(index, line, folder, blank_file_extensions, mpaths.pak01_dir):
                                                blacklist_data.append(path)
                                            continue

                                        elif line.startswith('>>'):
                                            for path in helper.processBlacklistDir(index, line, folder, mpaths.pak01_dir):
                                                blacklist_data.append(path)
                                            continue   

                                        else:
                                            if line.endswith(tuple(blank_file_extensions)):
                                                blacklist_data.append(line)
                                            else:
                                                helper.warnings.append(f"[Invalid Extension] '{line}' in 'mods\\{folder}\\blacklist.txt' [line: {index+1}] does not end in one of the valid extensions -> {blank_file_extensions}")
                                
                                # print(f"    blacklist.txt: Found {len(blacklist_data)} paths")

                                for index, line in enumerate(blacklist_data):
                                    line = line.strip()
                                    path, extension = os.path.splitext(line)

                                    # blacklist_dictionary["blacklist-key{}".format(index+1)] = path, extension

                                    if not os.path.exists(os.path.join(mpaths.game_dir, os.path.dirname(path))): os.makedirs(os.path.join(mpaths.game_dir, os.path.dirname(path)))

                                    try:
                                        shutil.copy(os.path.join(mpaths.blank_files_dir, 'blank{}').format(extension), os.path.join(mpaths.game_dir, path + extension))
                                    except FileNotFoundError as exception:
                                        helper.warnings.append(f"[Invalid Extension] '{line}' in 'mods\\{os.path.basename(mod_path)}\\blacklist.txt' does not end in one of the valid extensions -> {blank_file_extensions}")    

                                blacklist_data = []
                            # --------------------------------- styling.txt --------------------------------- #
                            if os.stat(styling_txt).st_size == 0: pass
                            else:
                                with open(styling_txt) as file:

                                    lines = file.readlines()

                                    for line in lines:
                                        line = line.strip()

                                        if line.startswith('#') or line.isspace():
                                            continue

                                        elif line.startswith('@@'):
                                            for path in helper.urlValidator(line):
                                                styling_data.append(path)
                                            continue
                                        else:
                                            styling_data.append(line)

                                # print(f"    styling.txt: Found styling.txt")

                                for index, line in enumerate(styling_data):
                                    try:
                                        line = line.split("@@")
                                        path = line[0].strip()
                                        style = line[1].strip()

                                        styling_dictionary["styling-key{}".format(index+1)] = path, style
                                                                                                
                                    except Exception as exception:
                                        helper.warnings.append("[{}]".format(type(exception).__name__) + " Could not validate '{}' in --> 'mods\\{}\\styling.txt' [line: {}]".format(line, folder, index+1))

                                    if not os.path.exists(os.path.join(mpaths.build_dir, os.path.dirname(path))): os.makedirs(os.path.join(mpaths.build_dir, os.path.dirname(path)))

                                    for key, value in list(styling_dictionary.items()):
                                        construct1 = Path(value[0], value[1])
                                        try:
                                            helper.vpkExtractor(construct1.path.vcss_c, mpaths.pak01_dir, mpaths.build_dir)
                                        except KeyError:
                                            helper.warnings.append("Path does not exist in VPK -> '{}', error in 'mods\\{}\\styling.txt'".format(construct1.path.vcss_c, folder))
                                            del styling_dictionary[key]
                                
                except Exception as exception:
                    exceptiondata = traceback.format_exc().splitlines()
                    helper.warnings.append(exceptiondata[-1])
            # ---------------------------------- STEP 2 ---------------------------------- #
            # ------------------- Decompile all files in "build" folder ------------------ #
            # ---------------------------------------------------------------------------- #
            print("→ Decompiling")
            with open(os.path.join(mpaths.logs_dir, 'decompiler.txt'), 'w') as file:
                subprocess.run([mpaths.minify_dir + '/Decompiler.exe', '--input', "build", '--recursive', '--vpk_decompile', '--output', "build"], stdout=file)
            # ---------------------------------- STEP 3 ---------------------------------- #
            # -------- Check what .css files are in "build" folder and write mods -------- #
            # ---------------------------------------------------------------------------- #
            print("→ Patching")
            for key, value in list(styling_dictionary.items()):
                construct2 = Path(value[0], value[1])
                
                with open(os.path.join(mpaths.build_dir, construct2.path.css), 'r+') as file: 
                    if construct2.style not in file.read():
                        file.write("\n" + construct2.style.strip())
            # ---------------------------------- STEP 4 ---------------------------------- #
            # -----------------  Move uncompiled files in build to content --------------- #
            # ---------------------------------------------------------------------------- #
            copytree(mpaths.build_dir, mpaths.content_dir, dirs_exist_ok=True, ignore=ignore_patterns("*.vcss_c"))
            # ---------------------------------- step 5 ---------------------------------- #
            # -------------- Compile content to game with resource compiler -------------- #
            # ---------------------------------------------------------------------------- #
            if helper.workshop_installed == True:
                with open(os.path.join(mpaths.logs_dir, 'resourcecompiler.txt'), 'wb') as file:
                    print("→ Compiling")
                    sp_compiler = subprocess.run([mpaths.resource_compiler, '-i', mpaths.content_dir + '/*', '-r'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if sp_compiler.stdout != b"":
                        file.write(sp_compiler.stdout)
                    
                    if sp_compiler.stderr != b"":
                        decoded_err = sp_compiler.stderr.decode("utf-8")
                        raise Exception(decoded_err)
            # ---------------------------------- STEP 6 ---------------------------------- #
            # -------- Create VPK from game folder and save into Minify directory -------- #
            # ---------------------------------------------------------------------------- #
            newpak = vpk.new(mpaths.game_dir)
            newpak.save(os.path.join(mpaths.dota_minify, 'pak01_dir.vpk'))

            patching = False
            helper.toggleFrameOn(self.checkboxesFrame, self.buttonsFrame, mpaths.mods_dir, mpaths.mods_folders, checkboxes)
            print("→ Done!")
            print("-------------------------------------------------------")
            print("Remember to add '-language minify' to dota2 launch options")
            print("Click Help button below for instructions")
            helper.handleWarnings(mpaths.logs_dir)

        except Exception:
            with open(os.path.join(mpaths.logs_dir, 'crashlog.txt'), 'w') as file:
                file.write(traceback.format_exc())

            patching = False
            helper.toggleFrameOn(self.checkboxesFrame, self.buttonsFrame, mpaths.mods_dir, mpaths.mods_folders, checkboxes)
            print("")
            print("Patching failed.")
            print("Check 'logs\\crashlog.txt' for more info.")
            print("-------------------------------------------------------")

if __name__ == '__main__':
    app = App()