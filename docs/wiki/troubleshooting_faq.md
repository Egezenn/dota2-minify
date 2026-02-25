## Safety

This project has been around since [2022](https://github.com/Egezenn/dota2-minify/commit/825ed37e6007577b98c3003fe0bdab6410ba87db) with thousands of downloads and users. While binaries are offered for ease of use, anyone can compile it themselves.

The only valid source to get the software is from [GitHub Releases](https://github.com/Egezenn/dota2-minify/releases/latest) or [the website](https://egezenn.github.io/dota2-minify). Releases are built via [GitHub Workflows](https://github.com/Egezenn/dota2-minify/blob/main/.github/workflows/release.yml) with no intervention, **we do not distribute elsewhere**.

No one has ever been banned for the use of these mods and alike. Minify strictly deals with VPK modifications and not hacking related concepts (memory/file manipulation).

### How

Minify utilizes Valve's approved methods for creating assets, as documented on the [official Valve Wiki](https://developer.valvesoftware.com/wiki/VPK). These are then enabled by a method that the game uses (low violence patches, voiceline localizations etc).

Historically Valve has only disabled assets from loading and some methods but have never punished modders using VPKs. The worst thing that can happen is a mod may stop working and that's it.

## Workshop Tools DLC

This allows Minify to create HUD/Interface mods, resource compilation while patching.

If you're seeing a mod that is grayed out, it requires this DLC.

### Downloading the DLC

- Right-click on Dota2 in Steam and click **Properties**.

![tools-instruction-1](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/tools-instruction-1.png)

- Select **Properties** > **DLC**.

> [!WARNING]
> On Linux, you need to force the use of `Proton Experimental` and have `wine` package installed. Relaunch steam if you still don't see the DLC.

![tools-instruction-2](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/tools-instruction-2.png)

- Install `Dota 2 Workshop Tools DLC`.
- Restart Minify.

> [!WARNING]
> For people using Minify on Linux with workshop tools!
>
> After patching, extract your workshop tools using the `Hammer button` > `Extract workshop tools` and go back to using a `Steam Runtime` as you'll not be able to queue into games with `Proton Experimental`.
>
> This copies the necessary files from the game onto Minify itself for convenience.

![tools-instruction-3](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/tools-instruction-3.png)

## Changing voiceline language

![language-voicelines](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/language-voicelines.png)

## Language parameter / nothing has changed

While newer versions automatically handle the parameter for you by new settings, you may have to change it yourself if it doesn't work.

![language-instruction-1](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/language-instruction-1.png)

![language-instruction-2](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/language-instruction-2.png)

- Right-click on Dota2 in Steam and click **Properties**.

![tools-instruction-1](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/tools-instruction-1.png)

- **English:** Add `-language minify` to your launch options.
- **Other Languages:** Select the language you want to patch with on the top bar and add `-language language_id`

![language-instruction-3](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/language-instruction-3.png)

## Antivirus software flagged it / I don't see an executable

Exclude the folder from your antivirus software(s).

### Why?

These are false-positives caused by people generating similiar compilation/hashes for malwares via the same compilers we're using and we don't have a signing certificate to resolve this as the project is relatively small.

### How do I trust it?

Binaries are released directly from GitHub's build system and there aren't any modifications done from us after releases. If you don't like the executables/archives we're providing, [you can run it with Python](development.md?id=running-from-the-source) or [build it completely yourself](development.md?id=compilation).

## VAC dialog

Verify your files from Steam, this happens every so often randomly and is NOT related to anything the program does.

## Things are broken!

Try uninstalling the mods. If that doesn't work aswell try using the feature below (it'll delete all the contents of `dota 2 beta/game/dota_<language>`!)

![clean-all-language-paths](https://github.com/Egezenn/dota2-minify/raw/main/docs/assets/wipe-language-paths.png)

## Not working / Crashes

Make a bug report on [GitHub](https://github.com/Egezenn/dota2-minify/issues) or [Discord](https://discord.com/invite/2YDnqpbcKM) with `minify_debug_<timestamp>.zip` that's created on crashes or the contents of your `logs` folder.
