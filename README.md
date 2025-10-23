# Grades Service

A simple containerized service for teachers to track grades across multiple courses. Built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**, this API lets you create courses, register students, enroll them, define assignments (quizzes, tests, projects) and record grades. You can also bulk‑import grades from CSV files and compute assignment statistics on the fly.

## Features

• **Course management** – create and list courses by code, title and term.  
• **Student management** – add students with unique email addresses and names.  
• **Enrollments** – associate students with courses.  
• **Assignments** – define quizzes, tests and projects per course, with maximum points.  
• **Grades** – upsert points for each student on each assignment, with validation.  
• **Bulk upload** – import grades from a CSV file (`course_code,student_email,assignment_name,points`).  
• **Statistics** – retrieve the average, minimum, maximum and count of scores for a specific assignment.  
• **Admin interface** – use Adminer at `localhost:8080` to inspect the database (`db` server, user `grades`, password `grades`, database `grades`).

## Getting Started

You’ll need Docker and Docker Compose installed. Clone this repository and run the following commands from its root:

```bash
# start the services (API, database and Adminer)
docker compose up --build

