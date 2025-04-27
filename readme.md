# <div align="center">Dota2 Minify</div>

<div align="center">
  <img src="bin/images/logo.png" alt="logo" width="150">
</div>

<br>

<div align="center">

  ![license](https://img.shields.io/github/license/Egezenn/dota2-minify?style=for-the-badge)
  <a href="https://discord.com/invite/2YDnqpbcKM"><img alt="badge" src="https://img.shields.io/badge/Discord-%237289DA.svg?style=for-the-badge&logo=discord&logoColor=white"></a>
  <a href="https://github.com/Egezenn/dota2-minify/wiki"><img alt="badge" src="https://img.shields.io/badge/github_wiki-%23000000.svg?style=for-the-badge&logo=github"></a>

  ![latest-release](https://img.shields.io/github/v/release/Egezenn/dota2-minify?style=for-the-badge)
  ![build-state](https://img.shields.io/github/actions/workflow/status/Egezenn/dota2-minify/release.yml?style=for-the-badge)

  ![downloads](https://img.shields.io/github/downloads/Egezenn/dota2-minify/total?style=for-the-badge)
  ![downloads-latest](https://img.shields.io/github/downloads/Egezenn/dota2-minify/latest/total?style=for-the-badge)

  ![commits-since](https://img.shields.io/github/commits-since/Egezenn/dota2-minify/latest?style=for-the-badge)

</div>

**<h3 align="center">All in one smart patcher for Dota2 to install all types of mods</h3>**

**<h3 align="center">Updated to 7.38!</h3>**

<div align="center">
  ✔️500+ Spells Simplified • ✔️8,000+ files modded • ✔️Boost FPS • ✔️ Creator Toolkit
</div>

<div align="center">
    <a href="#"><img alt="ss1" src="bin/images/screenshot-1.jpg"></a>
    <a href="#"><img alt="ss2" src="bin/images/screenshot-2.jpg"></a>
</div>

## Is this safe to use?

This project has been around for over 3 years with thousands of downloads and users. While binaries are offered for ease of use, anyone can compile it themselves.

No one has ever been banned for these mods. This project strictly deals with VPK modifications and not hacking related things like memory/file manipulation. It is utilizing Valve's approved methods (VPK loading) for creating assets, as documented on the [official Valve Wiki](https://developer.valvesoftware.com/wiki/VPK). Historically Valve has only disabled assets from loading and never punished modders. The worst thing that can happen is a mod stops working and that's it.

## Installation

1. **Download Minify**

   - [Click here to download the latest Minify release](https://github.com/Egezenn/dota2-minify/releases/latest)

    **(Optional) Install Dota 2 Workshop Tools DLC**
    - These tools enable HUD/Interface mods. **Skip this step if you don't need them.**
    - Right-click on Dota 2 in Steam.
    - Select **Properties** > **DLC**.
    - Install **"Dota 2 Workshop Tools DLC"**.

2. **Run Minify**

   - Extract the ZIP file.
   - Run `Minify.exe` and patch with the mods you want to use.

3. **Set Language for Steam**

   - Right-click on Dota2 in Steam and click **Properties**.
   - **For English Dota2:** Add `-language minify` to your launch options.
   - **For Other Languages:** Follow the [instructions here](https://github.com/Egezenn/dota2-minify/wiki/Minify#using-minify-with-a-different-language-in-dota2).

4. **Start Dota 2**
     - Launch Dota2 and enjoy!

### Optional Setup

#### Using the project locally

- `git clone https://github.com/Egezenn/dota2-minify`
- `cd dota2-minify`
- `python -m venv .venv`
- `.venv\Scripts\activate.bat` or `source .venv/bin/activate`
- `pip install -r requirements.txt`
- `python imgui.py`

#### Compilation from source

For instructions, refer to [here](https://github.com/Egezenn/dota2-minify/wiki/Minify#compiling-minify).

## Developing Your Own Mods

You can create your own mods with Minify

[The wiki](https://github.com/Egezenn/dota2-minify/wiki/Dota2-Modding-Tutorials) will teach you the basics of working with steam files and more.

Once you get comfortable with the workflow you can use Minify to easily patch latest files from Dota2 and always have your mods updated.

## Minify File Structure [>> tutorial](https://github.com/Egezenn/dota2-minify/wiki/Minify)

| Name                                                                                | Description                                                                                   |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| [`Files`](https://github.com/Egezenn/dota2-minify/wiki/Minify#files)                | Compiled files you want to pack (Models, Meshes, Textures...etc)                              |
| [`blacklist.txt`](https://github.com/Egezenn/dota2-minify/wiki/Minify#blacklisttxt) | _Paths_ to files to replace with blanks so they wont appear in game (Particles, Sounds...etc) |
| [`styling.txt`](https://github.com/Egezenn/dota2-minify/wiki/Minify#stylingtxt)     | Custom CSS you want to apply to the Panorama (Interfaces, Layouts, HUD's...etc)               |
| `notes_<local>.txt`                                                                 | Include this file to have a details button beside your mod for users to read.                 |

## Thanks

This project wouldn't be available without the work of the community. Thanks to everyone that has contributed to the project over [GitHub](https://github.com/Egezenn/dota2-minify/graphs/contributors) or [Discord](https://discord.com/invite/2YDnqpbcKM)!

## Special thanks to

### [robbyz512](https://github.com/robbyz512)

Creation of the base project.

<details>
<summary>Mods</summary>

- `Dark Terrain`
- `Minify Base Attacks`
- `Minify HUD`
- `Minify Spells & Items`
- `Misc Optimization`
- `Mute Ambient Sounds`
- `Mute Taunt Sounds`
- `Mute Voice Line Sounds`
- `Remove Foilage`
- `Remove Pinging`
- `Remove River`
- `Remove Sprays`
- `Remove Weather Effects`
- `Tree Mod`

</details>

### [Egezenn](https://github.com/Egezenn)

Taking over the maintainership of the project, implementing automated workflows, improving the functionality, Linux port, Turkish translations and [more](https://github.com/Egezenn/dota2-minify/commits/main/?author=Egezenn).

<details>
<summary>Mods</summary>

- `Mute Announcers`
- [`OpenDotaGuides Guides`](https://github.com/Egezenn/OpenDotaGuides)
- `Remove Laggy UI`
- `Remove Main Menu Background`
- `Stat Site Buttons In Profiles`
- `Transparent HUD` improvements
- Snippets in `User Styles`

</details>

### [ZerdacK](https://github.com/DotaModdingCommunity)

Rewrite of the GUI, Russian translations, mod fixes and [more](https://github.com/Egezenn/dota2-minify/commits/main/?author=DotaModdingCommunity).

<details>
<summary>Mods</summary>

- `Transparent HUD`

</details>

### [MeGaNeKoS](https://github.com/MeGaNeKoS)

<details>
<summary>Mods</summary>

- `Dotabuff in Profiles` mod which has been refactored to `Stat Site Buttons In Profiles`
- `Show NetWorth mod`

</details>

### [otf31](https://github.com/otf31)

Spanish translation.

## Dependencies

### Binaries

[Python](https://www.python.org/) - Core language. Licensed under PSFL license.

[Source 2 Viewer](https://github.com/ValveResourceFormat/ValveResourceFormat) - Used in decompilation of contents in paks. Licensed under MIT license.

### Python packages

[dearpygui](https://github.com/hoffstadt/DearPyGui) Used in the GUI. Licensed under MIT license.

[Nuitka](https://nuitka.net/) Used in compilation of the binaries. Licensed under Apache-2.0 license.

[psutil](https://github.com/giampaolo/psutil) Used in handling processes. Licensed under BSD-3-Clause license.

[requests](https://github.com/psf/requests) Used in downloading/querying project's dependencies. Licensed under Apache-2.0 license.

[screeninfo](https://github.com/rr-/screeninfo) Used in calculating initial position for the main window. Licensed under MIT license.

[vpk](https://github.com/ValvePython/vpk) Used in creating and getting file content list in VPKs. Licensed under MIT license.
