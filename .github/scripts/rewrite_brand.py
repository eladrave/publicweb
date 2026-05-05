#!/usr/bin/env python3
"""Rewrite the legacy brand name across repository text and path names."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OLD = "Cy" + "napsa"
NEW_TEXT = "Rave Tech"
NEW_IDENT = "RaveTech"
NEW_LOWER_IDENT = "ravetech"
OLD_SHORT = "cy" + "n"
NEW_SHORT = "rt"

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".next",
    ".nuxt",
    ".turbo",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "vendor",
}

CASELESS_OLD = re.compile(re.escape(OLD), re.IGNORECASE)
CASELESS_OLD_SHORT = re.compile(
    r"(?<![A-Za-z0-9])" + re.escape(OLD_SHORT) + r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)


def is_identifier_char(value: str) -> bool:
    return bool(value) and (value.isalnum() or value in {"_", "$"})


def replacement_for_text(match: re.Match[str]) -> str:
    token = match.group(0)
    before = match.string[match.start() - 1] if match.start() > 0 else ""
    after = match.string[match.end()] if match.end() < len(match.string) else ""
    in_identifier = is_identifier_char(before) or is_identifier_char(after)

    if token.islower():
        return NEW_LOWER_IDENT
    if token.isupper():
        return NEW_TEXT.upper() if not in_identifier else NEW_IDENT.upper()
    return NEW_IDENT if in_identifier else NEW_TEXT


def replacement_for_path(match: re.Match[str]) -> str:
    token = match.group(0)
    if token.islower():
        return NEW_LOWER_IDENT
    if token.isupper():
        return NEW_IDENT.upper()
    return NEW_IDENT


def replacement_for_short(match: re.Match[str]) -> str:
    return NEW_SHORT.upper() if match.group(0).isupper() else NEW_SHORT


def should_skip_dir(path: Path) -> bool:
    return path.name in SKIP_DIRS


def text_files() -> list[Path]:
    files: list[Path] = []
    for current_root, dirs, names in os.walk(ROOT):
        root_path = Path(current_root)
        dirs[:] = [name for name in dirs if not should_skip_dir(root_path / name)]
        for name in names:
            files.append(root_path / name)
    return files


def rewrite_file(path: Path) -> bool:
    raw = path.read_bytes()
    if b"\0" in raw:
        return False

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False

    rewritten = CASELESS_OLD.sub(replacement_for_text, text)
    rewritten = CASELESS_OLD_SHORT.sub(replacement_for_short, rewritten)
    if rewritten == text:
        return False

    newline = b"\n" if raw.endswith(b"\n") else b""
    path.write_bytes(rewritten.encode("utf-8"))
    if newline and not path.read_bytes().endswith(newline):
        path.write_bytes(path.read_bytes() + newline)
    return True


def rewrite_path_name(path: Path) -> Path:
    if not CASELESS_OLD.search(path.name) and not CASELESS_OLD_SHORT.search(path.name):
        return path
    name = CASELESS_OLD.sub(replacement_for_path, path.name)
    name = CASELESS_OLD_SHORT.sub(replacement_for_short, name)
    return path.with_name(name)


def rename_paths() -> list[tuple[Path, Path]]:
    renamed: list[tuple[Path, Path]] = []
    paths = sorted(
        [path for path in ROOT.rglob("*") if ".git" not in path.parts],
        key=lambda item: len(item.parts),
        reverse=True,
    )

    for path in paths:
        if not path.exists():
            continue
        target = rewrite_path_name(path)
        if target == path:
            continue
        if target.exists():
            raise FileExistsError(f"Cannot rename {path} to {target}: target exists")
        path.rename(target)
        renamed.append((path, target))
    return renamed


def main() -> int:
    changed = [path for path in text_files() if rewrite_file(path)]
    renamed = rename_paths()

    for path in changed:
        print(f"rewrote {path.relative_to(ROOT)}")
    for old, new in renamed:
        print(f"renamed {old.relative_to(ROOT)} -> {new.relative_to(ROOT)}")
    if not changed and not renamed:
        print("No brand references found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
