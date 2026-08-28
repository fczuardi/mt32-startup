from pathlib import Path
import tomllib

PORT = 1999
DEFAULT_PATH = "profiles/everyday.toml"
DEFAULT_HOST = "192.168.0.105"


def blank(path=DEFAULT_PATH):
    return {
        "path": path,
        "name": Path(path).stem,
        "host": DEFAULT_HOST,
        "port": PORT,
        "soundfont": "",
        "rows": [(channel, {}) for channel in range(1, 17)],
    }


def load(path):
    with Path(path).open("rb") as handle:
        data = tomllib.load(handle)

    device = data.get("device") or {}
    rows = [(channel, {}) for channel in range(1, 17)]
    for raw_channel, config in sorted((data.get("channels") or {}).items(), key=lambda item: int(item[0])):
        channel = int(raw_channel)
        if not 1 <= channel <= 16:
            raise ValueError(f"channels.{channel} must be 1..16")
        rows[channel - 1] = (channel, config)

    return {
        "path": path,
        "name": (data.get("profile") or {}).get("name") or Path(path).stem,
        "host": device.get("host") or missing("profile needs [device] host"),
        "port": int(device.get("port", PORT)),
        "soundfont": (data.get("soundfont") or {}).get("pi_name", ""),
        "rows": rows,
    }


def latest():
    paths = sorted(Path("profiles").glob("*.toml"), key=lambda path: path.stat().st_mtime)
    return str(paths[-1]) if paths else None


def save(data):
    lines = [
        "[device]",
        f"host = {quote(data['host'])}",
        f"port = {data['port']}",
        "",
        "[profile]",
        f"name = {quote(data['name'])}",
        "",
        "[soundfont]",
        f"pi_name = {quote(data['soundfont'])}",
        "",
    ]
    for channel, config in data["rows"]:
        lines.append(f"[channels.{channel}]")
        if "program" in config:
            lines += [
                f"bank = {config.get('bank', 0)}",
                f"program = {config['program']}",
                f"name = {quote(config.get('name', ''))}",
            ]
        lines.append("")
    Path(data["path"]).parent.mkdir(parents=True, exist_ok=True)
    Path(data["path"]).write_text("\n".join(lines), encoding="utf-8")


def quote(value):
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def missing(message):
    raise ValueError(message)
