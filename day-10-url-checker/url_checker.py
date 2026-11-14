# Author: Mashhood Ali
"""URL health checker.

Checks a list of URLs and reports which ones are alive, which redirect,
and which are broken. Useful for auditing links in a README, a docs site,
or a bookmarks file before you share it.

Features:
  - Concurrent checks with a thread pool (fast on long lists)
  - HEAD first, automatic GET fallback for servers that reject HEAD
  - Follows redirects and reports the final URL and redirect count
  - Retries transient failures (429 / 5xx / timeouts) with backoff
  - Table, JSON, or CSV output; exit code 1 when any URL is broken

Usage:
    python3 url_checker.py https://example.com https://github.com
    python3 url_checker.py --file urls.txt --workers 20
    python3 url_checker.py https://example.com --json --output report.json
    python3 url_checker.py --file urls.txt --csv
"""

import argparse
import concurrent.futures
import csv
import json
import ssl
import sys
import time
import urllib.error
import urllib.request

DEFAULT_TIMEOUT = 10
DEFAULT_WORKERS = 10
DEFAULT_RETRIES = 2
RETRYABLE_STATUS = {408, 425, 429, 500, 502, 503, 504}

# Status bands shown in the table output.
STATUS_LABELS = {
    "ok": "OK",
    "redirect": "REDIRECT",
    "client_error": "CLIENT ERROR",
    "server_error": "SERVER ERROR",
    "error": "ERROR",
}


class RedirectRecorder(urllib.request.HTTPRedirectHandler):
    """Counts redirects and remembers the final URL of each request."""

    def __init__(self):
        super().__init__()
        self.redirects = 0
        self.final_url = None

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        self.redirects += 1
        self.final_url = newurl
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def classify(status):
    """Map an HTTP status code to a result band."""
    if 200 <= status < 300:
        return "ok"
    if 300 <= status < 400:
        return "redirect"
    if 400 <= status < 500:
        return "client_error"
    return "server_error"


def build_opener(insecure):
    """Build an opener that records redirects (and optionally skips TLS checks).

    Returns (opener, recorder); keep the recorder reference, because
    build_opener prepends its own default handlers ahead of ours.
    """
    recorder = RedirectRecorder()
    handlers = [recorder]
    if insecure:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        handlers.append(urllib.request.HTTPSHandler(context=ctx))
    return urllib.request.build_opener(*handlers), recorder


def fetch_once(opener, recorder, url, timeout, method):
    """One request attempt. Returns (status, final_url, redirects, error)."""
    recorder.redirects = 0
    recorder.final_url = None
    request = urllib.request.Request(url, method=method)
    request.add_header("User-Agent", "url-checker/1.0")
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, recorder.final_url or url, recorder.redirects, None
    except urllib.error.HTTPError as exc:
        # HTTPError still carries a real status code (404, 500, ...).
        return exc.code, recorder.final_url or url, recorder.redirects, None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return None, url, recorder.redirects, str(reason)


def check_url(url, timeout, retries, insecure=False):
    """Check one URL with retries on transient failures.

    Builds its own opener per call: the redirect recorder holds per-request
    state, so sharing one opener across the thread pool would race.
    Returns a dict with the url, status, band, final url, redirect count,
    elapsed time in ms, and an error message (empty when the server answered).
    """
    opener, recorder = build_opener(insecure)
    started = time.monotonic()
    status, final_url, redirects, error = fetch_once(
        opener, recorder, url, timeout, "HEAD"
    )
    # Some servers reject HEAD (405/501); retry the same URL with GET.
    if status in (405, 501):
        status, final_url, redirects, error = fetch_once(
            opener, recorder, url, timeout, "GET"
        )
    attempts = 1
    while (status is None or status in RETRYABLE_STATUS) and attempts <= retries:
        time.sleep(0.5 * attempts)
        status, final_url, redirects, error = fetch_once(
            opener, recorder, url, timeout, "GET"
        )
        attempts += 1
    elapsed_ms = int((time.monotonic() - started) * 1000)
    band = classify(status) if status is not None else "error"
    return {
        "url": url,
        "status": status,
        "band": band,
        "final_url": final_url,
        "redirects": redirects,
        "elapsed_ms": elapsed_ms,
        "error": error or "",
        "attempts": attempts,
    }


def load_urls(args):
    """Collect URLs from --file and from positional arguments, in order."""
    urls = []
    if args.file:
        with open(args.file, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)
    urls.extend(args.urls)
    # De-duplicate while keeping the input order.
    seen = set()
    unique = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def print_table(results):
    """Print a fixed-width table of results, then a one-line summary."""
    rows = []
    for result in results:
        status = str(result["status"]) if result["status"] is not None else "-"
        rows.append(
            (
                STATUS_LABELS[result["band"]],
                status,
                f"{result['elapsed_ms']}ms",
                result["url"],
            )
        )
    widths = [max(len(row[i]) for row in rows) for i in range(4)]
    for label, status, elapsed, url in rows:
        print(
            f"{label:<13} {status:>{widths[1]}}  {elapsed:>{widths[2]}}  {url}"
        )
    print_summary(results)


def print_summary(results):
    """Print counts per band plus the total elapsed time."""
    counts = {}
    for result in results:
        counts[result["band"]] = counts.get(result["band"], 0) + 1
    total_ms = sum(result["elapsed_ms"] for result in results)
    parts = [f"{count} {STATUS_LABELS[band].lower()}" for band, count in counts.items()]
    print(f"\n{len(results)} URLs checked in {total_ms}ms: {', '.join(parts)}")


def output_json(results, path):
    """Write results (plus summary) as JSON to a file or stdout."""
    counts = {}
    for result in results:
        counts[result["band"]] = counts.get(result["band"], 0) + 1
    payload = {"results": results, "summary": counts}
    text = json.dumps(payload, indent=2)
    if path:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    else:
        print(text)


def output_csv(results, path):
    """Write results as CSV to a file or stdout."""
    fields = ["url", "status", "band", "final_url", "redirects", "elapsed_ms", "error"]
    target = open(path, "w", encoding="utf-8", newline="") if path else sys.stdout
    try:
        writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    finally:
        if path:
            target.close()


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Check a list of URLs and report which ones are broken."
    )
    parser.add_argument("urls", nargs="*", help="URLs to check")
    parser.add_argument("--file", help="file with one URL per line (# = comment)")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS,
                        help="concurrent checks (default: 10)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="seconds to wait per request (default: 10)")
    parser.add_argument("--retries", type=int, default=DEFAULT_RETRIES,
                        help="retries on transient failures (default: 2)")
    parser.add_argument("--insecure", action="store_true",
                        help="skip TLS certificate verification")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--json", action="store_true", help="output JSON")
    group.add_argument("--csv", action="store_true", help="output CSV")
    parser.add_argument("--output", help="write --json/--csv output to this file")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if args.workers < 1:
        print("error: --workers must be at least 1", file=sys.stderr)
        return 2
    if args.timeout <= 0:
        print("error: --timeout must be positive", file=sys.stderr)
        return 2
    if args.retries < 0:
        print("error: --retries must be at least 0", file=sys.stderr)
        return 2
    try:
        urls = load_urls(args)
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2
    if not urls:
        print("error: no URLs given (pass URLs or --file)", file=sys.stderr)
        return 2

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(
            pool.map(
                lambda url: check_url(url, args.timeout, args.retries, args.insecure),
                urls,
            )
        )
    # Keep output in input order even though checks ran concurrently.
    results.sort(key=lambda result: urls.index(result["url"]))

    if args.json:
        output_json(results, args.output)
    elif args.csv:
        output_csv(results, args.output)
    else:
        if args.output:
            print("error: --output needs --json or --csv", file=sys.stderr)
            return 2
        print_table(results)

    broken = any(result["band"] in ("client_error", "server_error", "error")
                 for result in results)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
