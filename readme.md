# <div align="center">Dota2 Minify</div>

<div align="center">
  <img src="bin/images/logo.png" alt="logo" width="150">
</div>

<br>

<div align="center">

  ![license](https://img.shields.io/github/license/Egezenn/dota2-minify?style=for-the-badge)
  [![discord](https://img.shields.io/badge/Discord-%237289DA.svg?style=for-the-badge&logo=discord&logoColor=white)](https://discord.com/invite/2YDnqpbcKM)
  [![wiki](https://img.shields.io/badge/github_wiki-%23000000.svg?style=for-the-badge&logo=github)](https://github.com/Egezenn/dota2-minify/wiki)

  ![latest-release](https://img.shields.io/github/v/release/Egezenn/dota2-minify?style=for-the-badge)
  ![build-state](https://img.shields.io/github/actions/workflow/status/Egezenn/dota2-minify/release.yml?style=for-the-badge)

  ![downloads](https://img.shields.io/github/downloads/Egezenn/dota2-minify/total?style=for-the-badge)
  ![downloads-latest](https://img.shields.io/github/downloads/Egezenn/dota2-minify/latest/total?style=for-the-badge)

</div>

**<h3 align="center">All in one smart patcher for Dota2 to install all types of mods</h3>**

**<h3 align="center">Updated to 7.38c!</h3>**

<div align="center">
  ✔️500+ Spells Simplified • ✔️8,000+ files modded • ✔️Boost FPS • ✔️ Creator Toolkit
</div>

<div align="center">
    <a href="#"><img alt="ss1" src="bin/images/screenshot-1.jpg"></a>
    <a href="#"><img alt="ss2" src="bin/images/screenshot-2.jpg"></a>
</div>

<hr>

## Is this safe to use?

This project has been around for over 3 years with thousands of downloads and users.

No one has ever been banned for these mods. This project strictly deals with VPK modifications and not hacking related things like memory/file manipulation. It is utilizing Valve's approved methods (VPK loading) for creating assets, as documented on the [official Valve Wiki](https://developer.valvesoftware.com/wiki/VPK). Historically Valve has only disabled assets from loading and never punished modders. The worst thing that can happen is a mod stops working and that's it.

### Malware allegations

If you haven't gotten the binaries from [here](https://github.com/Egezenn/dota2-minify/releases/latest) we can't assure you that what you had used was safe and not tampered with. Binaries provided here are strictly released with a [workflow](https://github.com/Egezenn/dota2-minify/blob/stable/.github/workflows/release.yml) to ensure the transparency of the whole process. You are welcome to take a gander.

## Installation

1. **Download Minify**

   - [Click here to download the latest Minify release](https://github.com/Egezenn/dota2-minify/releases/latest)

    **(Optional) Install Dota 2 Workshop Tools DLC**
    - These tools enable HUD/Interface mods.
    - Right-click on Dota 2 in Steam.
    - Select `Properties` > `DLC`.
    - Install `Dota 2 Workshop Tools DLC`

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

**Compile from Source**: If you prefer compiling the project yourself [Click here for instructions](https://github.com/Egezenn/dota2-minify/wiki/Minify#compiling-minify)

**External Binaries**: You need `Source2Viewer-CLI.exe` and it's dependent DLL's, if your OS is Windows, these are downloaded automatically once you run the project for the first time. If your OS is something else:

1. [Click here to go to SteamDatabase/ValveResourceFormat releases](https://github.com/SteamDatabase/ValveResourceFormat/releases/latest)
2. Download the file respective of your OS and CPU architecture
3. Extract the zip into your clone.

## Developing Your Own Mods

You can create your own mods with Minify

[The wiki](https://github.com/Egezenn/dota2-minify/wiki/Dota2-Modding-Tutorials) will teach you the basics of working with steam files and more.

Once you get comfortable with the workflow you can use Minify to easily patch latest files from Dota2 and always have your mods updated.

## Minify File Structure [>> tutorial](https://github.com/Egezenn/dota2-minify/wiki/Minify)

| Name                                                                                | Description                                                                                   |
|-------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [`Files`](https://github.com/Egezenn/dota2-minify/wiki/Minify#files)                | Compiled files you want to pack (Models, Meshes, Textures...etc)                              |
| [`blacklist.txt`](https://github.com/Egezenn/dota2-minify/wiki/Minify#blacklisttxt) | _Paths_ to files to replace with blanks so they wont appear in game (Particles, Sounds...etc) |
| [`styling.txt`](https://github.com/Egezenn/dota2-minify/wiki/Minify#stylingtxt)     | Custom CSS you want to apply to the Panorama (Interfaces, Layouts, HUD's...etc)               |
| `notes.txt`                                                                         | Optionally include this file to have a details button beside your mod for users to read.      |

## Thanks

This project wouldn't be available without the work of the community. Thanks to everyone that has contributed to the project over [GitHub](https://github.com/Egezenn/dota2-minify/graphs/contributors) or [Discord](https://discord.com/invite/2YDnqpbcKM)!
