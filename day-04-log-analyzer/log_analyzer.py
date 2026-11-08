# Author: Mashhood Ali
# Day 4 - Log Analyzer (Python)
# Reads a web server access log (Common / Combined Log Format) and
# prints a short operations summary: total requests, unique visitors,
# status code breakdown, busiest IPs and paths, and the error rate.
# Lines that do not parse are counted and skipped, not crashed on.
#
# Example line it understands:
# 203.0.113.7 - - [07/Nov/2026:10:00:01 +0500] "GET /index.html HTTP/1.1" 200 1024
#
# Stdlib only, no dependencies. Run it on any .log file.

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# One regex for the whole line: IP, timestamp, request, status, bytes.
LOG_PATTERN = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[[^\]]+\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<bytes>\S+)'
)


def parse_line(line):
    """Return (ip, method, path, status) or None if the line is malformed."""
    match = LOG_PATTERN.match(line.strip())
    if not match:
        return None
    return (
        match.group("ip"),
        match.group("method"),
        match.group("path"),
        int(match.group("status")),
    )


def analyze(lines):
    """Crunch parsed lines into summary counters."""
    total = 0
    skipped = 0
    ips = Counter()
    paths = Counter()
    statuses = Counter()
    errors = Counter()

    for line in lines:
        parsed = parse_line(line)
        if parsed is None:
            skipped += 1
            continue
        ip, method, path, status = parsed
        total += 1
        ips[ip] += 1
        paths[path] += 1
        statuses[status] += 1
        if status >= 400:
            errors[path] += 1

    error_count = sum(count for code, count in statuses.items() if code >= 400)
    return {
        "total": total,
        "skipped": skipped,
        "unique_ips": len(ips),
        "ips": ips,
        "paths": paths,
        "statuses": statuses,
        "errors": errors,
        "error_rate": (error_count / total * 100) if total else 0.0,
    }


def report(summary, top):
    """Print the summary in a fixed, readable order."""
    print(f"Total requests: {summary['total']}")
    print(f"Unique IPs: {summary['unique_ips']}")
    print(f"Skipped lines: {summary['skipped']}")
    print(f"Error rate (4xx + 5xx): {summary['error_rate']:.1f}%")
    print()
    print("Status codes:")
    for code in sorted(summary["statuses"]):
        print(f"  {code}: {summary['statuses'][code]}")
    print()
    print(f"Top {top} IPs:")
    for ip, count in summary["ips"].most_common(top):
        print(f"  {ip}: {count}")
    print()
    print(f"Top {top} paths:")
    for path, count in summary["paths"].most_common(top):
        print(f"  {path}: {count}")
    if summary["errors"]:
        print()
        print("Paths returning errors:")
        for path, count in summary["errors"].most_common(top):
            print(f"  {path}: {count}")


def main():
    parser = argparse.ArgumentParser(
        description="Summarize a web server access log."
    )
    parser.add_argument("logfile", help="path to the access log file")
    parser.add_argument(
        "--top", type=int, default=5, help="how many top IPs/paths to show (default 5)"
    )
    args = parser.parse_args()

    path = Path(args.logfile)
    if not path.is_file():
        print(f"Error: no such file: {args.logfile}", file=sys.stderr)
        sys.exit(1)

    with path.open(encoding="utf-8", errors="replace") as handle:
        summary = analyze(handle)

    if summary["total"] == 0:
        print("No valid log lines found.")
        sys.exit(0)

    report(summary, args.top)


if __name__ == "__main__":
    main()
