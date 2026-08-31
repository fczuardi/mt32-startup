# mt32 helpers

A small companion utility for configuring and initializing an [mt32-lupi](https://github.com/mo-g/mt32-lupi) device from another computer.

The immediate goal is deliberately modest: make a headless mt32-lupi setup nicer to use with a compact MIDI controller.

## Initial scope

These helpers aim to:

- choose between MT-32 emulation and SoundFont/FluidSynth mode;
- choose the active SoundFont;
- define useful bank/program assignments for MIDI channels 1–16;
- save those assignments as local profiles;
- apply channel assignments at runtime using mt32-lupi's raw UDP MIDI input;
- save channel assignments to per-SoundFont startup configs on patched firmware;
- update persistent mt32-lupi configuration over FTP when necessary.

## Why

Stock FluidSynth starts melodic MIDI channels on the default piano program (with channel 10 reserved for drums). On a controller that can switch MIDI channels directly, those channels can instead become a handy set of instant instrument bookmarks.

The current workaround is to send Bank Select / Program Change messages after mt32-lupi boots. On patched firmware, `mt32-startup` can also write those presets into the SoundFont's startup config.

## Current architecture idea

```text
MIDI controller
      |
      v
  mt32-lupi
      ^
      |
+-------------+
| mt32 helpers|
+-------------+
  |         |
  |         +--> FTP: persistent mt32-pi.cfg and SoundFont .cfg changes
  |
  +------------> UDP/1999: live MIDI Bank Select / Program Change
```

Channel favorites can be applied to the current session over UDP, or saved to the active SoundFont's startup `.cfg` on firmware that supports channel preset sections.

## Status

Early experiment / work in progress.

## v0 Usage

This project has two small `gum` entrypoints. Local `config.toml` and saved `profiles/*.toml` files are user data and are ignored by version control.

```bash
./mt32-favorites
```

`mt32-favorites` edits local channel favorite profiles, applies them to the current session over UDP/1999, and can save them to the active SoundFont's startup `.cfg` over FTP. Before showing the dashboard, it reads `/SD/mt32-pi.cfg` and `/SD/soundfonts` over FTP to identify the configured startup SoundFont, then matches that filename under your local SoundFont folder.

```bash
./mt32-config
```

`mt32-config` edits persistent boot behavior in `/SD/mt32-pi.cfg`, such as boot synth and startup SoundFont. It does not edit channel favorites.

`gum` is required:

```bash
sudo pacman -S gum
```

To inspect the MIDI bytes without touching the Pi:

```bash
./mt32-favorites --dry-run --apply-latest
```

To skip the dashboard and apply the newest profile:

```bash
./mt32-favorites --apply-latest
```

To temporarily allow any bank on any channel while testing firmware behavior:

```bash
./mt32-favorites --allow-any-bank
./mt32-favorites --allow-any-bank --apply-latest
```

Profiles are local TOML files. Use `Apply now` for runtime-only MIDI changes, or `Save to device startup` to write persistent channel presets for patched firmware.
