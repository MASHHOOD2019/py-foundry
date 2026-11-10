# Author: Mashhood Ali
# Day 6 - Duplicate File Finder (Python)
# Finds duplicate files under a folder and reports how much disk space
# they waste. Files are grouped by size first (cheap), then only files
# with the same size are hashed with SHA-256, so a big folder is scanned
# fast without reading every byte twice. With --delete it keeps the first
# file of each group and deletes the rest, but only after you confirm.
#
# Stdlib only, no dependencies.
#
# Usage:
#   python3 dup_finder.py ~/Downloads
#   python3 dup_finder.py ~/Pictures --min-size 1MB --json report.json
#   python3 dup_finder.py ~/Downloads --delete

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

# Read files in 1 MiB chunks so huge files never load into memory.
CHUNK_SIZE = 1024 * 1024

# Suffixes --min-size understands.
SIZE_UNITS = {"B": 1, "KB": 1024, "MB": 1024 ** 2, "GB": 1024 ** 3}


def parse_size(text):
    """Parse '500', '10KB', '1MB' or '2GB' into a byte count."""
    text = text.strip().upper()
    for unit, factor in SIZE_UNITS.items():
        if text.endswith(unit):
            number = text[: -len(unit)].strip()
            try:
                return int(float(number) * factor)
            except ValueError:
                raise argparse.ArgumentTypeError(
                    f"bad size: {text!r} (try 500, 10KB, 1MB, 2GB)"
                )
    try:
        return int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"bad size: {text!r} (try 500, 10KB, 1MB, 2GB)"
        )


def human_size(nbytes):
    """Format a byte count as '512 B', '2.4 KB', '1.1 MB' or '3.0 GB'."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if nbytes < 1024 or unit == "TB":
            return f"{nbytes:.1f} {unit}" if unit != "B" else f"{nbytes} B"
        nbytes /= 1024


def hash_file(path):
    """SHA-256 of a file, read in chunks. Returns None if unreadable."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            while chunk := handle.read(CHUNK_SIZE):
                digest.update(chunk)
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc}", file=sys.stderr)
        return None
    return digest.hexdigest()


def collect_files(root, min_size):
    """Walk root and return {size: [paths]} for regular files only.

    Symlinks are skipped (hashing a link would just re-hash its target),
    and unreadable entries are warned about and skipped.
    """
    by_size = defaultdict(list)
    scanned = 0
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError as exc:
            print(f"warning: cannot stat {path}: {exc}", file=sys.stderr)
            continue
        scanned += 1
        if size >= min_size:
            by_size[size].append(path)
    return by_size, scanned


def find_duplicates(root, min_size):
    """Return (groups, scanned, hashed).

    groups is a list of duplicate groups, each a list of Paths with
    identical content, sorted largest waste first.
    """
    by_size, scanned = collect_files(root, min_size)
    hashed = 0
    groups = []
    for size, paths in by_size.items():
        if len(paths) < 2:
            continue  # A unique size cannot be a duplicate.
        by_hash = defaultdict(list)
        for path in paths:
            digest = hash_file(path)
            hashed += 1
            if digest is not None:
                by_hash[digest].append(path)
        for same_content in by_hash.values():
            if len(same_content) > 1:
                groups.append(sorted(same_content))
    # Largest recoverable space first.
    groups.sort(key=lambda g: g[0].stat().st_size * (len(g) - 1), reverse=True)
    return groups, scanned, hashed


def main():
    parser = argparse.ArgumentParser(
        description="Find duplicate files and report wasted disk space."
    )
    parser.add_argument("directory", help="folder to scan (searched recursively)")
    parser.add_argument(
        "--min-size",
        type=parse_size,
        default=1,
        metavar="SIZE",
        help="ignore files smaller than SIZE, e.g. 10KB, 1MB (default: 1 byte)",
    )
    parser.add_argument(
        "--json",
        metavar="FILE",
        help="also write the duplicate groups as JSON to FILE",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="delete duplicates, keeping the first file of each group "
        "(asks for confirmation first)",
    )
    args = parser.parse_args()

    root = Path(args.directory).expanduser()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    groups, scanned, hashed = find_duplicates(root, args.min_size)

    duplicate_files = sum(len(g) - 1 for g in groups)
    wasted = sum(g[0].stat().st_size * (len(g) - 1) for g in groups)

    print(f"Scanned {scanned} files, hashed {hashed} same-size candidates.")
    if not groups:
        print("No duplicates found.")
        return 0

    print(f"Found {len(groups)} duplicate groups, "
          f"{duplicate_files} extra copies, "
          f"{human_size(wasted)} wasted.\n")
    for index, group in enumerate(groups, 1):
        size = group[0].stat().st_size
        print(f"Group {index} ({len(group)} copies, {human_size(size)} each):")
        for path in group:
            print(f"  {path}")
        print()

    if args.json:
        report = [
            {"size_bytes": g[0].stat().st_size, "files": [str(p) for p in g]}
            for g in groups
        ]
        try:
            Path(args.json).write_text(json.dumps(report, indent=2))
            print(f"Report written to {args.json}")
        except OSError as exc:
            print(f"warning: could not write {args.json}: {exc}", file=sys.stderr)

    if args.delete:
        answer = input(
            f"Delete {duplicate_files} duplicate files, keeping one per "
            f"group? [y/N] "
        ).strip().lower()
        if answer != "y":
            print("Aborted, nothing deleted.")
            return 0
        deleted = 0
        for group in groups:
            for path in group[1:]:
                try:
                    path.unlink()
                    deleted += 1
                except OSError as exc:
                    print(f"warning: could not delete {path}: {exc}",
                          file=sys.stderr)
        print(f"Deleted {deleted} duplicate files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
