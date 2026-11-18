from .database import db


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='active')  # active / inactive

    # deleting a course also deletes its examinations
    examinations = db.relationship('Examination', backref='course', lazy=True,
                                   cascade='all, delete-orphan')
