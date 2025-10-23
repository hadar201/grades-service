from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint, CheckConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base
import enum

class AssignmentType(str, enum.Enum):
    quiz = "quiz"
    test = "test"
    project = "project"

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    term: Mapped[str] = mapped_column(String(64))
    assignments = relationship("Assignment", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    enrollments = relationship("Enrollment", back_populates="student", cascade="all, delete-orphan")
    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")

class Enrollment(Base):
    __tablename__ = "enrollments"
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), primary_key=True)
    course = relationship("Course", back_populates="enrollments")
    student = relationship("Student", back_populates="enrollments")
    __table_args__ = (UniqueConstraint("course_id", "student_id", name="uq_enrollment"),)

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[AssignmentType] = mapped_column(Enum(AssignmentType))
    max_points: Mapped[int] = mapped_column(Integer)
    course = relationship("Course", back_populates="assignments")
    grades = relationship("Grade", back_populates="assignment", cascade="all, delete-orphan")
    __table_args__ = (UniqueConstraint("course_id", "name", name="uq_course_assignment"),)

class Grade(Base):
    __tablename__ = "grades"
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id"), primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), primary_key=True)
    points: Mapped[int] = mapped_column(Integer)
    assignment = relationship("Assignment", back_populates="grades")
    student = relationship("Student", back_populates="grades")
    __table_args__ = (
        CheckConstraint("points >= 0", name="ck_points_nonnegative"),
    )
