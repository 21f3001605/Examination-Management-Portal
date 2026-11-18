from .database import db

# Which examiners are assigned to which examination (many-to-many)
exam_examiners = db.Table(
    'exam_examiners',
    db.Column('exam_id', db.Integer, db.ForeignKey('examinations.id'), primary_key=True),
    db.Column('examiner_id', db.Integer, db.ForeignKey('examiner_profiles.id'), primary_key=True),
)


class Examination(db.Model):
    __tablename__ = 'examinations'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    exam_type = db.Column(db.String(30), nullable=False)   # Viva / Practical / Project Demo / Assessment
    duration_min = db.Column(db.Integer, nullable=False)
    max_marks = db.Column(db.Integer, nullable=False)

    slot_creation_start = db.Column(db.Date)
    slot_creation_end = db.Column(db.Date)
    booking_start = db.Column(db.Date)
    booking_end = db.Column(db.Date)

    # Draft / Slot Creation / Booking Open / Closed / Completed
    status = db.Column(db.String(20), nullable=False, default='Draft')
    results_published = db.Column(db.Boolean, default=False)

    rubrics = db.relationship('Rubric', backref='examination', lazy=True,
                              cascade='all, delete-orphan')
    slots = db.relationship('Slot', backref='examination', lazy=True,
                            cascade='all, delete-orphan')
    examiners = db.relationship('ExaminerProfile', secondary=exam_examiners,
                                backref='assigned_exams')
