from sqlalchemy.orm import Session
from sqlalchemy import select
from .database import engine, SessionLocal, Base
from . import models

def ensure_data(db: Session):
    # create tables
    Base.metadata.create_all(bind=engine)
    # sample course
    c = db.scalar(select(models.Course).where(models.Course.code=="CS101"))
    if not c:
        c = models.Course(code="CS101", title="Intro to CS", term="Fall 2025")
        db.add(c)
    # sample students
    for email, name in [("alice@example.com","Alice King"), ("bob@example.com","Bob Cohen")]:
        s = db.scalar(select(models.Student).where(models.Student.email==email))
        if not s:
            db.add(models.Student(email=email, full_name=name))
    db.commit()

if __name__ == "__main__":
    with SessionLocal() as db:
        ensure_data(db)
