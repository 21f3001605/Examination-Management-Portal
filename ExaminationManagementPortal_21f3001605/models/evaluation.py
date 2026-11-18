from datetime import datetime
from .database import db


class Evaluation(db.Model):
    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), unique=True, nullable=False)
    examiner_id = db.Column(db.Integer, db.ForeignKey('examiner_profiles.id'), nullable=False)
    total_marks = db.Column(db.Float, default=0)
    remarks = db.Column(db.Text)
    evaluated_at = db.Column(db.DateTime, default=datetime.now)

    scores = db.relationship('EvaluationScore', backref='evaluation', lazy=True,
                             cascade='all, delete-orphan')


# Marks for one rubric criterion inside an evaluation
class EvaluationScore(db.Model):
    __tablename__ = 'evaluation_scores'

    id = db.Column(db.Integer, primary_key=True)
    evaluation_id = db.Column(db.Integer, db.ForeignKey('evaluations.id'), nullable=False)
    rubric_id = db.Column(db.Integer, db.ForeignKey('rubrics.id'), nullable=False)
    marks = db.Column(db.Float, nullable=False)

    rubric = db.relationship('Rubric')
