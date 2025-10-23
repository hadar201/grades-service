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
```

The API will be available at [http://localhost:8000](http://localhost:8000) with interactive documentation at `/docs`. PostgreSQL runs on port **5432** and Adminer runs on port **8080**.

To tear down the services and remove the database volume, run:

```bash
docker compose down -v
```

### Running without Docker

To run the API directly on your machine:

1. Install Python 3.12 and PostgreSQL.
2. Create a database called `grades` and update `DATABASE_URL` in `backend/app/database.py` if necessary.
3. Install dependencies: `pip install -r backend/requirements.txt`.
4. Start the API: `uvicorn app.main:app --reload --port 8000` from the `backend/app` directory.

## API Overview

The API uses JSON for requests and responses. Below is a summary of endpoints with example payloads:

| Endpoint                                          | Method | Description                                                                                              |
|---------------------------------------------------|:------:|----------------------------------------------------------------------------------------------------------|
| `/courses`                                        |  POST  | Create a course. Payload: `{ "code":"CS101", "title":"Intro to CS", "term":"Fall 2025" }`             |
| `/courses`                                        |  GET   | List all courses.                                                                                        |
| `/students`                                       |  POST  | Add a student. Payload: `{ "email":"alice@example.com", "full_name":"Alice King" }`                 |
| `/students`                                       |  GET   | List all students.                                                                                       |
| `/enroll`                                         |  POST  | Enroll a student. Payload: `{ "course_code":"CS101", "student_email":"alice@example.com" }`        |
| `/assignments`                                    |  POST  | Create an assignment. Payload: `{ "course_code":"CS101", "name":"Quiz 1", "type":"quiz", "max_points":10 }` |
| `/courses/{course_code}/assignments`              |  GET   | List assignments for a course.                                                                           |
| `/grades`                                         |  POST  | Create or update a grade. Payload: `{ "course_code":"CS101", "assignment_name":"Quiz 1", "student_email":"alice@example.com", "points":9 }` |
| `/grades/upload`                                  |  POST  | Upload a CSV of grades using `multipart/form-data`. The file should have columns: `course_code,student_email,assignment_name,points`. |
| `/courses/{course_code}/assignments/{name}/stats` |  GET   | Get statistics (average, minimum, maximum and count) for a specific assignment.                         |

### CSV Formats

Prepare your CSV files with these headers:

• **students.csv** – `email,full_name`

• **courses.csv** – `code,title,term`

• **assignments.csv** – `course_code,name,type,max_points` (where `type` is one of `quiz`, `test`, or `project`)

• **grades.csv** – `course_code,student_email,assignment_name,points`

You can place these files in the `sample_data` directory and use the `/grades/upload` endpoint to import grades.

## Data Model

The service uses these tables (via SQLAlchemy):

| Table      | Columns                                                                      | Notes                                    |
|------------|-------------------------------------------------------------------------------|-------------------------------------------|
| **Course** | `id`, `code`, `title`, `term`                                                | `code` is unique                          |
| **Student**| `id`, `email`, `full_name`                                                   | `email` is unique                         |
| **Enrollment** | `course_id`, `student_id`                                                 | composite primary key; links students and courses |
| **Assignment** | `id`, `course_id`, `name`, `type`, `max_points`                          | unique name per course; type is an enum   |
| **Grade**  | `assignment_id`, `student_id`, `points`                                      | composite primary key; points ≥ 0         |

## Notes & Next Steps

This project is intentionally minimalist, serving as a foundation for a more complete gradebook system. You can extend it with features such as authentication, weighted categories, or a web frontend. Contributions and pull requests are welcome!
