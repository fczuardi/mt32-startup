from pathlib import Path
import tomllib

PATH = Path("config.toml")


def load():
    if not PATH.exists():
        return {}
    with PATH.open("rb") as handle:
        return tomllib.load(handle)


def soundfont_root():
    root = (load().get("soundfonts") or {}).get("root", "")
    return Path(root).expanduser() if root else None


def ftp():
    data = load().get("ftp") or {}
    return data.get("user", ""), data.get("password", "")


def save_soundfont_root(root):
    data = load()
    data["soundfonts"] = {"root": str(root)}
    save(data)


def save_ftp(user, password):
    data = load()
    data["ftp"] = {"user": user, "password": password}
    save(data)


def save(data):
    lines = []
    for section, values in data.items():
        lines.append(f"[{section}]")
        for key, value in values.items():
            lines.append(f"{key} = {quote(value)}")
        lines.append("")
    PATH.write_text("\n".join(lines), encoding="utf-8")


def quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'
