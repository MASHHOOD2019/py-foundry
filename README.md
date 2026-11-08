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
