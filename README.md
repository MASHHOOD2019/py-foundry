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
