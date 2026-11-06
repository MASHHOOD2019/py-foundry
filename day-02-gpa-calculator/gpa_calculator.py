# Author: Mashhood Ali
# Day 2 - GPA and CGPA Calculator (Python)
# Enter your courses and marks, it prints your semester GPA
# and your new CGPA. Works for any semester.

def points(marks):
    if marks >= 90:
        return 4.0
    elif marks >= 85:
        return 3.67
    elif marks >= 80:
        return 3.33
    elif marks >= 75:
        return 3.0
    elif marks >= 70:
        return 2.67
    elif marks >= 65:
        return 2.33
    elif marks >= 60:
        return 2.0
    elif marks >= 55:
        return 1.67
    elif marks >= 50:
        return 1.0
    else:
        return 0.0

old_cgpa = float(input("Your CGPA before this semester: "))
old_credits = int(input("Total credits completed before this semester: "))
old_points = old_cgpa * old_credits

n = int(input("How many courses this semester? "))

total_points = 0
total_credits = 0

for i in range(n):
    name = input("Course " + str(i + 1) + " name: ")
    credits = int(input("Credits: "))
    marks = int(input("Marks (0-100): "))
    p = points(marks)
    print(name, "-", marks, "marks, points:", p)
    total_points = total_points + p * credits
    total_credits = total_credits + credits

gpa = total_points / total_credits
new_points = old_points + total_points
new_credits = old_credits + total_credits
cgpa = new_points / new_credits

print("Semester GPA:", round(gpa, 2))
print("Semester points:", round(total_points, 2), "on", total_credits, "credits")
print("New CGPA:", round(cgpa, 2))
