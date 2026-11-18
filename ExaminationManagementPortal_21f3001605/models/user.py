from flask_login import UserMixin
from .database import db


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)                      
    status = db.Column(db.String(20), nullable=False, default='active') 
    examiner_profile = db.relationship('ExaminerProfile', backref='user', uselist=False,
                                       cascade='all, delete-orphan')
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False,
                                      cascade='all, delete-orphan')
