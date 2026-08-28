# mt32 helpers

A small companion utility for configuring and initializing an [mt32-lupi](https://github.com/mo-g/mt32-lupi) device from another computer.

The immediate goal is deliberately modest: make a headless mt32-lupi setup nicer to use with a compact MIDI controller, without requiring firmware changes.

## Initial scope

These helpers aim to:

- choose between MT-32 emulation and SoundFont/FluidSynth mode;
- choose the active SoundFont;
- define useful bank/program assignments for MIDI channels 1–16;
- save those assignments as local profiles;
- apply channel assignments at runtime using mt32-lupi's raw UDP MIDI input;
- update persistent mt32-lupi configuration over FTP when necessary.

## Why

Stock FluidSynth starts melodic MIDI channels on the default piano program (with channel 10 reserved for drums). On a controller that can switch MIDI channels directly, those channels can instead become a handy set of instant instrument bookmarks.

The current workaround is to send Bank Select / Program Change messages after mt32-lupi boots. `mt32-startup` is intended to make that setup repeatable and pleasant.

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
  |         +--> FTP: persistent mt32-pi.cfg changes
  |
  +------------> UDP/1999: live MIDI Bank Select / Program Change
```

For the first version, channel favorites are runtime state: they do not survive an mt32-lupi reboot, so `mt32-favorites` reapplies them when run.

## Status

Early experiment / work in progress.

## v0 Usage

This project has two small `gum` entrypoints. Local `config.toml` and saved `profiles/*.toml` files are user data and are ignored by version control.

```bash
./mt32-favorites
```

`mt32-favorites` edits local channel favorite profiles and applies them to the current session over UDP/1999. Before showing the dashboard, it reads `/SD/mt32-pi.cfg` and `/SD/soundfonts` over FTP to identify the configured startup SoundFont, then matches that filename under your local SoundFont folder.

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

Profiles are local TOML files. Runtime channel favorites are not persistent mt32-lupi configuration; rerun the command after the Pi reboots or reloads the synth.
