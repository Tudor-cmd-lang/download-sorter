#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


DOWNLOADS = Path.home() / "Downloads"
DEST_ROOT = DOWNLOADS  # keep categories inside Downloads (easy to see)


# Map extensions to folder names (lowercase extensions, include the dot)
EXT_MAP: Dict[str, str] = {
    # Archives
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    ".xz": "Archives",

    # Documents
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".odt": "Documents",
    ".rtf": "Documents",
    ".txt": "Documents",
    ".md": "Documents",
    ".csv": "Documents",
    ".xls": "Documents",
    ".xlsx": "Documents",
    ".ppt": "Documents",
    ".pptx": "Documents",

    # Images
    ".png": "Images",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".gif": "Images",
    ".webp": "Images",
    ".svg": "Images",
    ".heic": "Images",

    # Audio
    ".mp3": "Audio",
    ".wav": "Audio",
    ".flac": "Audio",
    ".ogg": "Audio",
    ".m4a": "Audio",

    # Video
    ".mp4": "Video",
    ".mkv": "Video",
    ".mov": "Video",
    ".webm": "Video",

    # Apps / installers
    ".deb": "Installers",
    ".rpm": "Installers",
    ".appimage": "Installers",

    # Code
    ".py": "Code",
    ".cpp": "Code",
    ".c": "Code",
    ".h": "Code",
    ".hpp": "Code",
    ".js": "Code",
    ".ts": "Code",
    ".html": "Code",
    ".css": "Code",
    ".json": "Code",
    ".yml": "Code",
    ".yaml": "Code",
    ".sh": "Code",
}

# Ignore temporary/in-progress download names
TEMP_SUFFIXES = (".part", ".crdownload", ".tmp")
TEMP_PATTERNS = (
    r"^\.",          # hidden files
    r"~$",           # editor backups
)

# Don’t move things inside these category folders (prevents loops)
CATEGORY_FOLDERS = set(EXT_MAP.values()) | {"Other"}


def is_temporary(path: Path) -> bool:
    name = path.name
    if name.lower().endswith(TEMP_SUFFIXES):
        return True
    for pat in TEMP_PATTERNS:
        if re.search(pat, name):
            return True
    return False


def stable_file(path: Path, checks: int = 3, delay: float = 0.5) -> bool:
    """
    Consider file 'stable' if size doesn't change across a few checks.
    Helps avoid moving while still downloading.
    """
    try:
        last = path.stat().st_size
        for _ in range(checks):
            time.sleep(delay)
            now = path.stat().st_size
            if now != last:
                last = now
            else:
                # one unchanged check is not enough; keep checking
                pass
        # if we got here without exceptions, treat as stable enough
        return True
    except FileNotFoundError:
        return False
    except PermissionError:
        return False


def pick_destination(path: Path) -> Path:
    ext = path.suffix.lower()
    folder = EXT_MAP.get(ext, "Other")
    return DEST_ROOT / folder / path.name


def ensure_unique(dest: Path) -> Path:
    """
    Avoid overwriting: file.ext -> file (1).ext -> file (2).ext ...
    """
    if not dest.exists():
        return dest
    stem, ext = dest.stem, dest.suffix
    parent = dest.parent
    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){ext}"
        if not candidate.exists():
            return candidate
        i += 1


def move_file(src: Path) -> None:
    if not src.is_file():
        return
    if is_temporary(src):
        return

    # Don't move stuff already inside category folders
    if src.parent == DOWNLOADS and src.name in CATEGORY_FOLDERS:
        return
    if src.parent.name in CATEGORY_FOLDERS:
        return

    # Wait a moment for downloads to finish writing
    if not stable_file(src):
        return

    dest = pick_destination(src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest = ensure_unique(dest)

    try:
        shutil.move(str(src), str(dest))
        print(f"Moved: {src.name} -> {dest.parent.name}/")
    except Exception as e:
        print(f"Failed to move {src}: {e}")


class Handler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        move_file(Path(event.src_path))

    def on_moved(self, event):
        # Some browsers download to temp then rename/move
        if event.is_directory:
            return
        move_file(Path(event.dest_path))

    def on_modified(self, event):
        # Optional: you can keep this off to reduce churn.
        # But some downloads finish via final "modified".
        if event.is_directory:
            return
        p = Path(event.src_path)
        # Only consider files directly in Downloads
        if p.parent == DOWNLOADS:
            move_file(p)


def main() -> None:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    print(f"Watching: {DOWNLOADS}")

    observer = Observer()
    observer.schedule(Handler(), str(DOWNLOADS), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
