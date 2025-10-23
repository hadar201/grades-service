from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
import csv, io

from .database import Base, engine, get_db
from . import models, schemas

app = FastAPI(title="Grades Service")

# Auto-create tables on startup (simple for a mini-project)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def health():
    return {"ok": True}

# --- Courses ---
@app.post("/courses", response_model=schemas.CourseOut)
def create_course(payload: schemas.CourseCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(models.Course).where(models.Course.code == payload.code))
    if existing:
        raise HTTPException(400, "Course code already exists")
    course = models.Course(code=payload.code, title=payload.title, term=payload.term)
    db.add(course); db.commit(); db.refresh(course)
    return course

@app.get("/courses", response_model=list[schemas.CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return db.scalars(select(models.Course).order_by(models.Course.code)).all()

# --- Students ---
@app.post("/students", response_model=schemas.StudentOut)
def create_student(payload: schemas.StudentCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(models.Student).where(models.Student.email == payload.email))
    if existing:
        raise HTTPException(400, "Student email already exists")
    s = models.Student(email=payload.email, full_name=payload.full_name)
    db.add(s); db.commit(); db.refresh(s)
    return s

@app.get("/students", response_model=list[schemas.StudentOut])
def list_students(db: Session = Depends(get_db)):
    return db.scalars(select(models.Student).order_by(models.Student.email)).all()

# --- Enrollments ---
@app.post("/enroll")
def enroll(payload: schemas.EnrollmentCreate, db: Session = Depends(get_db)):
    course = db.scalar(select(models.Course).where(models.Course.code == payload.course_code))
    student = db.scalar(select(models.Student).where(models.Student.email == payload.student_email))
    if not course or not student:
        raise HTTPException(404, "Course or student not found")
    exists = db.get(models.Enrollment, {"course_id": course.id, "student_id": student.id})
    if exists:
        return {"status": "already_enrolled"}
    db.add(models.Enrollment(course_id=course.id, student_id=student.id))
    db.commit()
    return {"status": "enrolled"}

# --- Assignments ---
@app.post("/assignments", response_model=schemas.AssignmentOut)
def create_assignment(payload: schemas.AssignmentCreate, db: Session = Depends(get_db)):
    course = db.scalar(select(models.Course).where(models.Course.code == payload.course_code))
    if not course:
        raise HTTPException(404, "Course not found")
    existing = db.scalar(select(models.Assignment).where(
        models.Assignment.course_id == course.id,
        models.Assignment.name == payload.name
    ))
    if existing:
        raise HTTPException(400, "Assignment name already exists in course")
    a = models.Assignment(course_id=course.id, name=payload.name, type=payload.type, max_points=payload.max_points)
    db.add(a); db.commit(); db.refresh(a)
    return a

@app.get("/courses/{course_code}/assignments", response_model=list[schemas.AssignmentOut])
def list_assignments(course_code: str, db: Session = Depends(get_db)):
    course = db.scalar(select(models.Course).where(models.Course.code == course_code))
    if not course:
        raise HTTPException(404, "Course not found")
    return db.scalars(select(models.Assignment).where(models.Assignment.course_id == course.id).order_by(models.Assignment.name)).all()

# --- Grades ---
@app.post("/grades", response_model=schemas.GradeOut)
def upsert_grade(payload: schemas.GradeCreate, db: Session = Depends(get_db)):
    course = db.scalar(select(models.Course).where(models.Course.code == payload.course_code))
    student = db.scalar(select(models.Student).where(models.Student.email == payload.student_email))
    if not course or not student:
        raise HTTPException(404, "Course or student not found")
    assignment = db.scalar(select(models.Assignment).where(
        models.Assignment.course_id == course.id,
        models.Assignment.name == payload.assignment_name
    ))
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    if payload.points > assignment.max_points:
        raise HTTPException(400, "Points cannot exceed max_points")

    grade = db.get(models.Grade, {"assignment_id": assignment.id, "student_id": student.id})
    if grade:
        grade.points = payload.points
    else:
        grade = models.Grade(assignment_id=assignment.id, student_id=student.id, points=payload.points)
        db.add(grade)
    db.commit(); db.refresh(grade)
    return grade

# --- CSV Upload for Grades ---
# CSV columns: course_code,student_email,assignment_name,points
@app.post("/grades/upload")
def upload_grades(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))
    updated, created, errors = 0, 0, []
    for i, row in enumerate(reader, start=2):
        try:
            payload = schemas.GradeCreate(**{
                "course_code": row["course_code"].strip(),
                "student_email": row["student_email"].strip(),
                "assignment_name": row["assignment_name"].strip(),
                "points": int(row["points"])
            })
            # reuse logic
            course = db.scalar(select(models.Course).where(models.Course.code == payload.course_code))
            student = db.scalar(select(models.Student).where(models.Student.email == payload.student_email))
            if not course or not student:
                raise ValueError("Course or student not found")
            assignment = db.scalar(select(models.Assignment).where(
                models.Assignment.course_id == course.id,
                models.Assignment.name == payload.assignment_name
            ))
            if not assignment:
                raise ValueError("Assignment not found")
            if payload.points > assignment.max_points:
                raise ValueError("points > max_points")
            grade = db.get(models.Grade, {"assignment_id": assignment.id, "student_id": student.id})
            if grade:
                grade.points = payload.points; updated += 1
            else:
                db.add(models.Grade(assignment_id=assignment.id, student_id=student.id, points=payload.points)); created += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})
    db.commit()
    return {"created": created, "updated": updated, "errors": errors}

# --- Simple stats per assignment ---
@app.get("/courses/{course_code}/assignments/{name}/stats", response_model=schemas.CourseStats)
def assignment_stats(course_code: str, name: str, db: Session = Depends(get_db)):
    course = db.scalar(select(models.Course).where(models.Course.code == course_code))
    if not course:
        raise HTTPException(404, "Course not found")
    assignment = db.scalar(select(models.Assignment).where(
        models.Assignment.course_id == course.id, models.Assignment.name == name
    ))
    if not assignment:
        raise HTTPException(404, "Assignment not found")
    q = select(
        func.avg(models.Grade.points),
        func.min(models.Grade.points),
        func.max(models.Grade.points),
        func.count(models.Grade.points)
    ).where(models.Grade.assignment_id == assignment.id)
    avg_, min_, max_, count_ = db.execute(q).one()
    return schemas.CourseStats(
        course_code=course_code, assignment_name=name,
        avg=float(avg_ or 0), min=int(min_ or 0), max=int(max_ or 0), count=int(count_ or 0)
    )
