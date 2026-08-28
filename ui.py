from pathlib import Path
import shutil
import subprocess


def require_gum():
    if not shutil.which("gum"):
        raise ValueError("gum is required")


def choose(header, items, height=16):
    result = subprocess.run(
        ["gum", "choose", "--height", str(height), "--header", header, *items],
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip() or cancel()


def input_text(header, password=False):
    command = ["gum", "input", "--header", header]
    if password:
        command.append("--password")
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE)
    return result.stdout.strip() or cancel()


def folder(header):
    result = subprocess.run(
        ["gum", "file", str(Path.home()), "--directory", "--file=false", "--header", header],
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout.strip() or cancel()


def box(lines):
    subprocess.run(["gum", "style", "--border", "normal", "--padding", "1 2", "\n".join(lines)])


def confirm(message):
    return subprocess.run(["gum", "confirm", message]).returncode == 0


def cancel():
    raise SystemExit(130)
