from datetime import datetime
from .database import db


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('slots.id'), nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), nullable=False, default='Booked')  # Booked / Cancelled / Completed

    evaluation = db.relationship('Evaluation', backref='booking', uselist=False,
                                 cascade='all, delete-orphan')
