from pydantic import BaseModel, EmailStr, Field
from .models import AssignmentType  # reuse the Enum from models

# --- Courses ---
class CourseCreate(BaseModel):
    code: str
    title: str
    term: str

class CourseOut(CourseCreate):
    id: int
    class Config:
        from_attributes = True

# --- Students ---
class StudentCreate(BaseModel):
    email: EmailStr
    full_name: str

class StudentOut(StudentCreate):
    id: int
    class Config:
        from_attributes = True

# --- Enrollment ---
class EnrollmentCreate(BaseModel):
    course_code: str
    student_email: EmailStr

# --- Assignments ---
class AssignmentCreate(BaseModel):
    course_code: str
    name: str
    type: AssignmentType           # Enum, not Literal
    max_points: int = Field(ge=1)

class AssignmentOut(BaseModel):
    id: int
    course_id: int
    name: str
    type: AssignmentType           # Enum, not Literal
    max_points: int
    class Config:
        from_attributes = True

# --- Grades ---
class GradeCreate(BaseModel):
    course_code: str
    assignment_name: str
    student_email: EmailStr
    points: int = Field(ge=0)

class GradeOut(BaseModel):
    assignment_id: int
    student_id: int
    points: int
    class Config:
        from_attributes = True

# --- Stats ---
class CourseStats(BaseModel):
    course_code: str
    assignment_name: str
    avg: float
    min: int
    max: int
    count: int
