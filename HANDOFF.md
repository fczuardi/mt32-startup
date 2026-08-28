# Handoff for local Codex

This repository is an early companion utility for [mt32-lupi](https://github.com/mo-g/mt32-lupi).

The goal is not to replace mt32-lupi or fork its firmware yet. The first useful version should make a headless mt32-lupi box easier to initialize and use from another computer, especially with compact MIDI controllers.

## Context

A Raspberry Pi 3 running mt32-lupi was tested successfully with:

- USB MIDI input from an Arturia MicroLab;
- FluidSynth / SoundFont mode;
- MT-32 emulation via Munt ROMs;
- Wi-Fi networking;
- FTP access to the SD-card filesystem;
- raw UDP MIDI on port `1999`.

The MicroLab can switch its outgoing MIDI channel directly with `Shift + one of the first 16 piano keys`. That makes the 16 MIDI channels useful as instant instrument bookmarks.

Stock FluidSynth starts melodic channels on Program 0 (piano), while channel 10 is percussion. We verified that sending Program Change messages over raw UDP changes those channel assignments at runtime.

## Important verified behavior

### Raw UDP MIDI

mt32-lupi accepts raw MIDI bytes via UDP port `1999`.

This was tested successfully from Python.

Example: Program Change, MIDI channel 1, program 16:

```python
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(bytes([0xC0, 16]), ("192.168.0.105", 1999))
```

Example: Note On / Note Off, middle C on channel 1:

```python
import socket
import time

addr = ("192.168.0.105", 1999)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.sendto(bytes([0x90, 60, 100]), addr)
time.sleep(1)
sock.sendto(bytes([0x80, 60, 0]), addr)
```

Do **not** hard-code `192.168.0.105` in the program. It was only the address of the test device. The target must be configurable.

### 16-channel favorites prototype

A simple script was tested successfully with a mapping like:

```python
favorites = {
    1: 0,    # Acoustic Grand Piano
    2: 4,    # Electric Piano 1
    3: 16,   # Drawbar Organ
    4: 24,   # Acoustic Guitar (nylon)
    5: 32,   # Acoustic Bass
    6: 40,   # Violin
    7: 48,   # String Ensemble 1
    8: 56,   # Trumpet
    9: 64,   # Soprano Sax
    # 10 is normally drums
    11: 73,  # Flute
    12: 80,  # Lead 1
    13: 88,  # Pad 1
    14: 52,  # Choir Aahs
    15: 11,  # Vibraphone
    16: 38,  # Synth Bass 1
}
```

For each entry, send:

```python
status = 0xC0 | (channel - 1)
sock.sendto(bytes([status, program]), (host, 1999))
```

These assignments are runtime state and are lost when mt32-lupi reboots or resets/reloads the synth.

### FTP

mt32-lupi exposes an embedded FTP server when enabled in `mt32-pi.cfg`.

FTP is useful for persistent configuration changes such as:

- `default_synth`;
- default SoundFont index;
- network settings;
- adding/removing SoundFonts and ROM files.

It is **not** a live MIDI transport.

The server is intentionally simple. Avoid assumptions about advanced FTP capabilities or multiple concurrent connections.

### SoundFonts

A typical tested `soundfonts/` directory contained:

```text
Arachno SoundFont - Version 1.0.sf2
FluidR3 GM.sf2
GeneralUser-GS.sf2
```

mt32-lupi selects a SoundFont by index. The exact ordering/index behavior should be verified from upstream source/docs before implementing anything that modifies the default SoundFont.

Do not assume that the user's local SoundFont collection matches this list.

### MT-32 mode

MT-32 and SoundFont mode are separate synth modes.

The tested ROM folder included valid old/new MT-32 and CM-32L ROM pairs. This project should not distribute copyrighted ROMs.

The utility should eventually allow choosing the startup synth mode, but the first milestone can focus on SoundFont mode and channel favorites.

## Arturia MicroLab observations

These details motivated the project but should **not** be hard-coded into the generic architecture.

Observed with `aseqdump`:

```text
Shift + piano keys 1..16 -> changes MIDI output channel 1..16
Shift + Octave Down      -> CC28, values 127 then 0
Shift + Octave Up        -> CC29, values 127 then 0
normal Mod strip         -> CC1, absolute 0..127
shifted Mod strip        -> relative-style CC114/CC115 messages
```

Examples of shifted-strip relative values:

```text
swipe up:   65, 66, 67...
swipe down: 63, 62, 60...
```

A future firmware or MIDI-mapping feature could interpret these as previous/next program navigation. That is **not required for v0**.

## RTP-MIDI experiment

RTP-MIDI was explored using `rtpmidid` on Linux. A direct peer could be created, but the mt32-lupi endpoint never completed the AppleMIDI handshake in the tested setup:

```text
status: WAITING
connection_count: 0
sent > 0
recv: 0
```

Because raw UDP MIDI worked immediately and reliably, **do not use RTP-MIDI in the first implementation**.

It can be revisited later if there is a clear benefit.

## Proposed v0

Build a very small local program that:

1. loads a local profile;
2. targets a configurable mt32-lupi hostname/IP;
3. sends Bank Select / Program Change messages via UDP/1999 for channels 1–16;
4. optionally leaves channel 10 alone as drums;
5. gives clear success/failure output;
6. has no firmware dependency beyond stock mt32-lupi network MIDI support.

The first implementation should work from the CLI before adding a TUI.

Example desired usage:

```bash
mt32-startup apply everyday
```

or initially:

```bash
python -m mt32_startup apply profiles/everyday.toml
```

## Profile format

Keep it boring and human-editable. TOML is a reasonable default because modern Python has `tomllib` in the standard library.

Possible shape:

```toml
[device]
host = "mt32-pi.local"
port = 1999

[profile]
name = "everyday"

[channels.1]
bank = 0
program = 0
name = "Grand Piano"

[channels.2]
bank = 0
program = 4
name = "Electric Piano"

[channels.3]
bank = 0
program = 16
name = "Drawbar Organ"

[channels.10]
drums = true
```

The `name` fields are informational. MIDI values are authoritative.

Do not require all 16 channels to be present. Missing channels should be left untouched.

## Bank Select

Program Change alone was tested. The implementation should also support bank selection correctly.

Normal MIDI bank selection uses:

- CC0: Bank Select MSB
- CC32: Bank Select LSB
- followed by Program Change

Do not confuse mt32-lupi's SoundFont-file index with a MIDI bank number inside an SF2.

A clean API might be:

```python
send_bank_program(channel, bank_msb, bank_lsb, program)
```

If the profile exposes a simplified single `bank` integer, document exactly how it maps to MSB/LSB. Prefer explicit MSB/LSB internally.

## TUI direction

The eventual UI idea is a small TUI, possibly using [gum](https://github.com/charmbracelet/gum), where the user can:

- choose SoundFont vs MT-32 mode;
- choose an available SoundFont;
- assign 16 favorite bank/program combinations;
- save profiles locally;
- apply the runtime channel mapping.

Do not start with a large framework. A CLI plus a simple profile is the first milestone.

## Persistent configuration

Later, add optional FTP support for settings that mt32-lupi already stores in `mt32-pi.cfg`.

Important design distinction:

```text
FTP / mt32-pi.cfg
    -> persistent device configuration

UDP MIDI
    -> live synth state
```

Do not pretend runtime channel favorites are persistent on stock firmware.

A future mt32-lupi upstream feature could add configurable startup channel mappings and/or generic MIDI-action mappings. If that lands upstream, this utility could write those values through FTP instead of reapplying them after boot.

## Non-goals for v0

Do not implement yet:

- firmware modifications;
- RTP-MIDI;
- SysEx abstraction layers;
- SF2 editing;
- SoundFont preset parsing unless needed by a later UI;
- DAW/plugin integration;
- automatic controller-specific mappings;
- ROM downloading or redistribution;
- a universal MIDI router.

## Suggested first commits

### Commit 1: core UDP MIDI

Create a small Python package/module with:

- configurable host/port;
- `send_program_change()`;
- `send_bank_select()`;
- `apply_profile()`;
- useful validation for channels 1..16 and MIDI values 0..127.

Add unit tests that inspect generated MIDI bytes without requiring hardware.

### Commit 2: TOML profiles

Add profile parsing with a checked-in example profile.

Keep dependencies at zero if practical (`tomllib`, `socket`, `argparse`).

### Commit 3: CLI

Support something like:

```bash
mt32-startup apply profiles/example.toml
```

and optionally:

```bash
mt32-startup test-note --host mt32-pi.local
```

### Commit 4: optional TUI exploration

Only after the CLI behavior is solid, evaluate `gum` as a thin interactive layer.

## Acceptance criteria for the first usable milestone

On a stock mt32-lupi device in SoundFont mode:

1. user runs one local command;
2. the tool sends the configured MIDI messages to UDP/1999;
3. switching the controller among MIDI channels plays the configured instruments;
4. channel 10 can remain percussion;
5. no SD-card removal is required;
6. no mt32-lupi firmware modification is required;
7. rebooting the Pi resets the assignments, and the documentation states this clearly;
8. rerunning the command restores them.

## Coding style

Favor a tiny, readable program over abstraction.

This repository started from hands-on exploration, so keep behavior easy to test from a terminal and document any assumption that comes from mt32-lupi rather than standard MIDI.
