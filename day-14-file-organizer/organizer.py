#!/usr/bin/env python3
"""Smart File Organizer.

Sorts the loose files in a directory into category subfolders by
extension (Images, Documents, Audio, Video, Archives, Code, Other).

Features:
  --dry-run     preview every move without touching anything
  --recursive   also organize files inside subfolders
  --undo        reverse the moves recorded in the undo log
  collision-safe: never overwrites; appends _1, _2, ... to the name
  undo log: a JSON manifest of every move, written next to the target

Stdlib only, no dependencies.

Usage:
  python3 organizer.py ~/Downloads
  python3 organizer.py ~/Downloads --dry-run
  python3 organizer.py ~/Downloads --recursive
  python3 organizer.py ~/Downloads --undo
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

CATEGORIES = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp",
               ".tif", ".tiff", ".ico", ".heic"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".rst", ".odt",
                  ".rtf", ".xls", ".xlsx", ".csv", ".tsv", ".ppt", ".pptx",
                  ".odp", ".ods", ".epub"},
    "Audio": {".mp3", ".wav", ".flac", ".ogg", ".oga", ".m4a", ".aac",
              ".wma", ".opus"},
    "Video": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm",
              ".m4v", ".3gp"},
    "Archives": {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
                 ".tgz", ".zst"},
    "Code": {".py", ".js", ".ts", ".java", ".c", ".h", ".cpp", ".hpp",
             ".cs", ".go", ".rs", ".rb", ".php", ".html", ".css", ".json",
             ".xml", ".yml", ".yaml", ".sh", ".sql"},
}
DEFAULT_CATEGORY = "Other"
LOG_NAME = ".organizer_undo.json"

EXT_TO_CATEGORY = {}
for _name, _exts in CATEGORIES.items():
    for _ext in _exts:
        EXT_TO_CATEGORY[_ext] = _name


def category_for(path):
    """Return the category name for a file based on its extension."""
    return EXT_TO_CATEGORY.get(path.suffix.lower(), DEFAULT_CATEGORY)


def unique_destination(dest, reserved=()):
    """Return dest, or dest with _1, _2, ... appended, so nothing is
    ever overwritten and no two planned moves share a destination."""
    taken = set(reserved)
    if dest not in taken and not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    counter = 1
    while True:
        candidate = dest.with_name(f"{stem}_{counter}{suffix}")
        if candidate not in taken and not candidate.exists():
            return candidate
        counter += 1


def iter_loose_files(target, recursive):
    """Yield files to organize. Skips the undo log itself and, in
    non-recursive mode, anything already inside a subfolder (which
    includes files already sorted into category folders)."""
    if recursive:
        candidates = (p for p in target.rglob("*") if p.is_file())
    else:
        candidates = (p for p in target.iterdir() if p.is_file())
    for path in candidates:
        if path.name == LOG_NAME:
            continue
        if recursive and path.parent.name in CATEGORIES:
            continue  # already organized
        yield path


def plan_moves(target, recursive):
    """Build the list of (source, destination) moves."""
    moves = []
    reserved = set()
    for src in sorted(iter_loose_files(target, recursive)):
        dest_dir = target / category_for(src)
        dest = unique_destination(dest_dir / src.name, reserved)
        reserved.add(dest)
        moves.append((src, dest))
    return moves


def load_log(target):
    log_path = target / LOG_NAME
    if not log_path.exists():
        return []
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"error: cannot read undo log {log_path}: {exc}")
    if not isinstance(data, list):
        raise SystemExit(f"error: undo log {log_path} is not a move list")
    return data


def save_log(target, moves):
    log_path = target / LOG_NAME
    log_path.write_text(json.dumps(moves, indent=2), encoding="utf-8")


def do_organize(target, recursive, dry_run):
    moves = plan_moves(target, recursive)
    if not moves:
        print("Nothing to organize: no loose files found.")
        return 0

    counts = {}
    for src, dest in moves:
        counts[dest.parent.name] = counts.get(dest.parent.name, 0) + 1
        rel_src = src.relative_to(target)
        rel_dest = dest.relative_to(target)
        verb = "would move" if dry_run else "moved"
        print(f"{verb}: {rel_src} -> {rel_dest}")

    if dry_run:
        print(f"\nDry run: {len(moves)} file(s) would be organized. "
              "Nothing was moved.")
        return 0

    record = load_log(target)
    for src, dest in moves:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        record.append({"from": str(src), "to": str(dest)})
    save_log(target, record)

    print(f"\nOrganized {len(moves)} file(s):")
    for name in sorted(counts):
        print(f"  {name}: {counts[name]}")
    print(f"Undo log written to {target / LOG_NAME}")
    return 0


def do_undo(target):
    record = load_log(target)
    if not record:
        print("Nothing to undo: no moves recorded.")
        return 0

    restored, missing = 0, 0
    for entry in reversed(record):
        src, dest = Path(entry["to"]), Path(entry["from"])
        if not src.exists():
            print(f"skipped (missing): {src}")
            missing += 1
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        final = unique_destination(dest)
        shutil.move(str(src), str(final))
        print(f"restored: {src.relative_to(target)} -> "
              f"{final.relative_to(target)}")
        restored += 1

    (target / LOG_NAME).unlink()
    print(f"\nUndo complete: {restored} file(s) restored, "
          f"{missing} missing. Undo log removed.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Sort loose files into category subfolders by "
                    "extension, with dry-run preview and undo.")
    parser.add_argument("directory", help="directory to organize")
    parser.add_argument("--dry-run", action="store_true",
                        help="preview the moves without changing anything")
    parser.add_argument("--recursive", action="store_true",
                        help="also organize files inside subfolders")
    parser.add_argument("--undo", action="store_true",
                        help="reverse the moves recorded in the undo log")
    args = parser.parse_args(argv)

    target = Path(args.directory).expanduser()
    if not target.exists():
        print(f"error: directory does not exist: {target}",
              file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"error: not a directory: {target}", file=sys.stderr)
        return 2
    target = target.resolve()

    try:
        if args.undo:
            return do_undo(target)
        return do_organize(target, args.recursive, args.dry_run)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
