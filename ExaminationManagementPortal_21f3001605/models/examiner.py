from .database import db


class ExaminerProfile(db.Model):
    __tablename__ = 'examiner_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))

    slots = db.relationship('Slot', backref='examiner', lazy=True)
    evaluations = db.relationship('Evaluation', backref='examiner', lazy=True)
