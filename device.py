from ftplib import FTP
from io import BytesIO

CONFIG = "/SD/mt32-pi.cfg"


def state(host, user, password):
    with FTP(host, timeout=5) as ftp:
        ftp.login(user or "anonymous", password)
        config = download_text(ftp, CONFIG)
        fonts = soundfonts_from(ftp)

    default_synth = config_value(config, "system", "default_synth", "mt32")
    soundfont_index = int(config_value(config, "fluidsynth", "soundfont", "0"))
    soundfont = fonts[soundfont_index] if soundfont_index < len(fonts) else fonts[0]
    return {
        "config": config,
        "default_synth": default_synth,
        "soundfont": soundfont,
        "soundfont_index": soundfont_index,
        "soundfonts": fonts,
    }


def write_config(host, user, password, text):
    with FTP(host, timeout=5) as ftp:
        ftp.login(user or "anonymous", password)
        ftp.storbinary("STOR " + CONFIG, BytesIO(text.encode("utf-8")))


def soundfonts_from(ftp):
    ftp.cwd("/SD/soundfonts")
    names = sorted(name for name in ftp.nlst() if name.lower().endswith(".sf2"))
    if not names:
        raise ValueError("no .sf2 files found in /SD/soundfonts")
    return names


def download_text(ftp, path):
    out = BytesIO()
    ftp.retrbinary("RETR " + path, out.write)
    return out.getvalue().decode("utf-8", errors="replace")


def config_value(text, section, key, default):
    current = ""
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
        if current == section and line.split("=", 1)[0].strip() == key:
            return line.split("=", 1)[1].strip()
    return default


def set_config_value(text, section, key, value):
    lines = text.splitlines()
    current = ""
    section_seen = False
    for index, line in enumerate(lines):
        stripped = line.split("#", 1)[0].strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if section_seen:
                lines.insert(index, f"{key} = {value}")
                return "\n".join(lines) + "\n"
            current = stripped[1:-1].strip()
            section_seen = current == section
        if current == section and "=" in stripped and stripped.split("=", 1)[0].strip() == key:
            lines[index] = f"{key} = {value}"
            return "\n".join(lines) + "\n"

    lines += ["", f"[{section}]", f"{key} = {value}"]
    return "\n".join(lines) + "\n"
