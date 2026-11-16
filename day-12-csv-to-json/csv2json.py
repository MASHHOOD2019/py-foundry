# Author: Mashhood Ali
"""CSV to JSON converter.

Converts a CSV file to a JSON array (or one JSON object per line with
--jsonl). Built for the everyday case of handing a spreadsheet export to
an API, a script, or a database import without opening a spreadsheet app.

Features:
  - Automatic delimiter detection (comma, tab, semicolon, pipe)
  - Type inference: integers, floats, booleans and empty cells become
    null, unless --no-infer keeps everything as strings
  - Dotted headers become nested objects: "address.city" nests under
    "address" instead of staying a flat key
  - Column selection (--columns) and renaming (--rename old=new)
  - Streams row by row, so large files do not load into memory
  - Reads from a file or stdin, writes to a file or stdout
  - Bad rows are reported and skipped instead of aborting the run

Usage:
    python3 csv2json.py data.csv
    python3 csv2json.py data.csv --jsonl --output data.jsonl
    python3 csv2json.py data.csv --columns name,age --rename age=years
    python3 csv2json.py --delimiter ";" --no-infer data.csv
    cat data.csv | python3 csv2json.py --indent 2
"""

import argparse
import csv
import io
import itertools
import json
import sys

DEFAULT_DELIMITERS = ",\t;|"
TRUE_VALUES = {"true", "yes", "y", "1"}
FALSE_VALUES = {"false", "no", "n", "0"}


def infer_value(raw):
    """Convert one CSV cell to the most specific JSON type that fits."""
    text = raw.strip()
    if text == "":
        return None
    lowered = text.lower()
    if lowered in TRUE_VALUES:
        return True
    if lowered in FALSE_VALUES:
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return raw


def set_nested(record, dotted_key, value):
    """Assign value under a dotted key, creating nested dicts as needed."""
    parts = dotted_key.split(".")
    target = record
    for part in parts[:-1]:
        target = target.setdefault(part, {})
        if not isinstance(target, dict):
            raise ValueError(
                "conflicting keys: '%s' is both a value and a group"
                % dotted_key
            )
    target[parts[-1]] = value


def build_record(row, headers, columns, renames, infer):
    """Turn one CSV row (dict) into the output JSON object."""
    record = {}
    for header in headers:
        if columns is not None and header not in columns:
            continue
        value = row.get(header, "")
        if infer:
            value = infer_value(value)
        key = renames.get(header, header)
        if "." in key:
            set_nested(record, key, value)
        else:
            record[key] = value
    return record


def sniff_delimiter(sample, explicit):
    """Detect the delimiter from a text sample, or use the explicit one."""
    if explicit:
        return explicit
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=DEFAULT_DELIMITERS)
        return dialect.delimiter
    except csv.Error:
        return ","


def parse_rename(spec):
    """Parse one old=new rename spec into a (old, new) pair."""
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            "rename must look like old=new, got '%s'" % spec
        )
    old, new = spec.split("=", 1)
    if not old or not new:
        raise argparse.ArgumentTypeError(
            "rename must look like old=new, got '%s'" % spec
        )
    return old, new


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Convert a CSV file to JSON."
    )
    parser.add_argument(
        "input", nargs="?", default="-",
        help="CSV file to read (default: stdin)",
    )
    parser.add_argument(
        "--output", "-o", default="-",
        help="file to write JSON to (default: stdout)",
    )
    parser.add_argument(
        "--jsonl", action="store_true",
        help="write one JSON object per line instead of an array",
    )
    parser.add_argument(
        "--indent", type=int, default=None,
        help="indent level for pretty output (JSON array mode only)",
    )
    parser.add_argument(
        "--delimiter", "-d", default=None,
        help="force a delimiter instead of auto-detecting it",
    )
    parser.add_argument(
        "--encoding", default="utf-8-sig",
        help="input encoding (default: utf-8-sig, strips a BOM)",
    )
    parser.add_argument(
        "--columns", default=None,
        help="comma-separated list of columns to keep, in order",
    )
    parser.add_argument(
        "--rename", action="append", type=parse_rename, default=[],
        metavar="OLD=NEW",
        help="rename a column (repeatable)",
    )
    parser.add_argument(
        "--no-infer", action="store_true",
        help="keep every value a string, no type inference",
    )
    parser.add_argument(
        "--skip-rows", type=int, default=0,
        help="data rows to skip before converting (default: 0)",
    )
    return parser.parse_args(argv)


def open_input(path, encoding):
    if path == "-":
        return sys.stdin
    return open(path, "r", encoding=encoding, newline="")


def open_output(path):
    if path == "-":
        return sys.stdout
    return open(path, "w", encoding="utf-8")


def convert(args):
    columns = (
        [c.strip() for c in args.columns.split(",")]
        if args.columns
        else None
    )
    renames = dict(args.rename)

    with open_input(args.input, args.encoding) as source:
        sample = source.read(8192)
        if source is sys.stdin:
            # stdin cannot be rewound: re-feed the sample, then the rest.
            source = itertools.chain(io.StringIO(sample), source)
        else:
            source.seek(0)
        delimiter = sniff_delimiter(sample, args.delimiter)
        reader = csv.DictReader(source, delimiter=delimiter)
        headers = reader.fieldnames
        if not headers:
            print("error: no header row found", file=sys.stderr)
            return 2
        if columns:
            unknown = [c for c in columns if c not in headers]
            if unknown:
                print(
                    "error: unknown column(s): %s" % ", ".join(unknown),
                    file=sys.stderr,
                )
                return 2

        converted = 0
        skipped = 0
        with open_output(args.output) as dest:
            first = True
            if not args.jsonl:
                dest.write("[")
                if args.indent is not None:
                    dest.write("\n")
            for index, row in enumerate(reader):
                if index < args.skip_rows:
                    continue
                if row is None or all(
                    (v is None or v.strip() == "") for v in row.values()
                ):
                    skipped += 1
                    continue
                try:
                    record = build_record(
                        row, headers, columns, renames, not args.no_infer
                    )
                except ValueError as exc:
                    print(
                        "warning: row %d skipped: %s" % (index + 2, exc),
                        file=sys.stderr,
                    )
                    skipped += 1
                    continue
                if args.jsonl:
                    dest.write(json.dumps(record, ensure_ascii=False))
                    dest.write("\n")
                else:
                    if not first:
                        dest.write(",")
                        if args.indent is not None:
                            dest.write("\n")
                    first = False
                    if args.indent is not None:
                        dumped = json.dumps(
                            record,
                            ensure_ascii=False,
                            indent=args.indent,
                        )
                        pad = " " * args.indent
                        dest.write(
                            pad + dumped.replace("\n", "\n" + pad)
                        )
                    else:
                        dest.write(
                            json.dumps(record, ensure_ascii=False)
                        )
                converted += 1
            if not args.jsonl:
                if args.indent is not None and converted:
                    dest.write("\n")
                dest.write("]\n")

    print(
        "Converted %d %s%s."
        % (
            converted,
            "row" if converted == 1 else "rows",
            " (%d skipped)" % skipped if skipped else "",
        ),
        file=sys.stderr,
    )
    return 0


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.indent is not None and args.jsonl:
        print(
            "error: --indent only applies to JSON array output",
            file=sys.stderr,
        )
        return 2
    try:
        return convert(args)
    except FileNotFoundError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2
    except (UnicodeDecodeError, csv.Error) as exc:
        print("error: could not read CSV: %s" % exc, file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
