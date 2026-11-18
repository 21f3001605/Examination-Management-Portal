from .database import db


# Name, email and status of the student are stored in the users table
class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    roll_no = db.Column(db.String(30), unique=True, nullable=False)

    bookings = db.relationship('Booking', backref='student', lazy=True)
