# py-foundry

One small Python program every day. No filler commits, no empty files.

## Day 2 - GPA and CGPA Calculator (Python)

`day-02-gpa-calculator/gpa_calculator.py`

Enter your previous CGPA and credits, then your courses with credits and
marks. It prints each course with its grade points, your semester GPA, and
your new CGPA. Works for any semester.

How to run:

```
python3 gpa_calculator.py
```

Example:

```
Your CGPA before this semester: 3.0
Total credits completed before this semester: 30
How many courses this semester? 3
Course 1 name: OOP
Credits: 3
Marks (0-100): 82
OOP - 82 marks, points: 3.33
...
Semester GPA: 2.89
New CGPA: 2.97
```

## Day 4 - Log Analyzer (Python)

`day-04-log-analyzer/log_analyzer.py`

Reads a web server access log and prints an operations summary: total
requests, unique IPs, status code breakdown, busiest IPs and paths, and
the error rate. Lines that do not parse are counted and skipped instead
of crashing the run. Stdlib only, no dependencies.

How to run:

```
python3 log_analyzer.py sample.log
python3 log_analyzer.py access.log --top 10
```

Example (on the included `sample.log`):

```
Total requests: 9
Unique IPs: 3
Skipped lines: 1
Error rate (4xx + 5xx): 33.3%

Status codes:
  200: 6
  404: 2
  500: 1

Top 5 IPs:
  203.0.113.7: 4
```

## Day 6 - Duplicate File Finder (Python)

`day-06-duplicate-finder/dup_finder.py`

Finds duplicate files under a folder and reports how much disk space
they waste. Files are grouped by size first, then only same-size files
are hashed with SHA-256, so big folders scan fast. With `--delete` it
keeps the first file of each group and deletes the rest, but only after
you confirm. Stdlib only, no dependencies.

How to run:

```
python3 dup_finder.py ~/Downloads
python3 dup_finder.py ~/Pictures --min-size 1MB --json report.json
python3 dup_finder.py ~/Downloads --delete
```

Example:

```
Scanned 6 files, hashed 5 same-size candidates.
Found 2 duplicate groups, 3 extra copies, 2.3 KB wasted.

Group 1 (3 copies, 1.2 KB each):
  /tmp/duptest/a.txt
  /tmp/duptest/b.txt
  /tmp/duptest/sub/c.txt
```

## Day 8 - Secure Password Generator (Python)

`day-08-password-generator/password_generator.py`

Generates cryptographically secure passwords with the `secrets` module
(never `random`, which is not safe for secrets). Every password is
guaranteed to contain at least one character from each selected set, and
each run reports the estimated entropy in bits with a strength rating.
Stdlib only, no dependencies.

How to run:

```
python3 password_generator.py
python3 password_generator.py --length 20 --count 5
python3 password_generator.py --length 12 --no-symbols --json
python3 password_generator.py --length 24 --exclude-ambiguous
```

Example:

```
*|vDXzySW0'*0!AZ

Entropy: 104.9 bits (Excellent) - pool of 94 characters, length 16
```

## Day 10 - URL Health Checker (Python)

`day-10-url-checker/url_checker.py`

Checks a list of URLs and reports which are alive, which redirect, and
which are broken. Checks run concurrently, HEAD first with an automatic
GET fallback, retries transient failures (429 / 5xx / timeouts) with
backoff, and follows redirects while reporting the final URL and redirect
count. Stdlib only, no dependencies. Exit code 1 when any URL is broken,
so it fits in a CI step or a pre-publish link audit.

How to run:

```
python3 url_checker.py https://example.com https://github.com
python3 url_checker.py --file urls.txt --workers 20
python3 url_checker.py https://example.com --json --output report.json
python3 url_checker.py --file urls.txt --csv
```

Example:

```
OK            200   789ms  https://example.com
OK            200   775ms  https://github.com
CLIENT ERROR  404   653ms  https://example.com/does-not-exist-xyz
ERROR           -  2863ms  https://nonexistent-domain-xyz12345.com

4 URLs checked in 5080ms: 2 ok, 1 client error, 1 error
```

## Day 12 - CSV to JSON Converter (Python)

`day-12-csv-to-json/csv2json.py`

Converts a CSV file to a JSON array, or one JSON object per line with
`--jsonl`, so a spreadsheet export can go straight into an API, a
script, or a database import. It auto-detects the delimiter (comma,
tab, semicolon, pipe), infers types (integers, floats, booleans,
empty cells become null), and turns dotted headers like
`address.city` into nested objects. Columns can be selected and
renamed, rows stream through without loading the file into memory,
and bad rows are reported and skipped instead of aborting the run.
Stdlib only, no dependencies.

How to run:

```
python3 csv2json.py data.csv
python3 csv2json.py data.csv --jsonl --output data.jsonl
python3 csv2json.py data.csv --columns name,age --rename age=years
python3 csv2json.py --delimiter ";" --no-infer data.csv
cat data.csv | python3 csv2json.py --indent 2
```

Example (on the included `sample.csv`):

```
[{"name": "Ayesha Khan", "age": 24, "active": true, "address": {"city": "Karachi", "zip": 75600}, "score": 91.5},{"name": "Bilal Ahmed", "age": 31, "active": false, "address": {"city": "Lahore", "zip": null}, "score": 78},{"name": "Sara Malik", "age": 19, "active": true, "address": {"city": "Islamabad", "zip": 44000}, "score": null}]
```

## Day 14 - Smart File Organizer (Python)

`day-14-file-organizer/organizer.py`

Sorts the loose files in a folder into category subfolders by
extension: Images, Documents, Audio, Video, Archives, Code, and
Other for anything unrecognized. It never overwrites: a name that
is already taken gets `_1`, `_2`, and so on appended. Every move is
recorded in a JSON undo log (`.organizer_undo.json`), so a run can
be fully reversed with `--undo`. Preview everything first with
`--dry-run`, and add `--recursive` to also sort files inside
subfolders. Stdlib only, no dependencies.

How to run:

```
python3 organizer.py ~/Downloads
python3 organizer.py ~/Downloads --dry-run
python3 organizer.py ~/Downloads --recursive
python3 organizer.py ~/Downloads --undo
```

Example:

```
moved: backup.zip -> Archives/backup.zip
moved: notes.txt -> Documents/notes.txt
moved: photo.jpg -> Images/photo.jpg
moved: song.mp3 -> Audio/song.mp3

Organized 4 file(s):
  Archives: 1
  Audio: 1
  Documents: 1
  Images: 1
```
