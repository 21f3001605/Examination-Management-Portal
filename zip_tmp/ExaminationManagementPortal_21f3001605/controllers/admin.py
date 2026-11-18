from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from utils import role_required
from models import db, User, Course, Examination, Rubric, Slot, Booking, ExaminerProfile, StudentProfile

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

EXAM_TYPES = ['Viva', 'Practical', 'Project Demo', 'Assessment']
EXAM_STATUSES = ['Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed']


# Runs before every /admin route, so each route doesn't need its own decorators
@admin_bp.before_request
@login_required
@role_required('admin')
def protect():
    pass


@admin_bp.route('/dashboard')
def dashboard():
    stats = {
        'Courses': Course.query.count(),
        'Examinations': Examination.query.count(),
        'Examiners': User.query.filter_by(role='examiner').count(),
        'Students': User.query.filter_by(role='student').count(),
        'Slots': Slot.query.count(),
        'Bookings': Booking.query.count(),
    }
    return render_template('admin/dashboard.html', stats=stats)


# ---------------- Courses ----------------

@admin_bp.route('/courses', methods=['GET', 'POST'])
def courses():
    if request.method == 'POST':
        code = request.form['code'].strip().upper()
        name = request.form['name'].strip()

        if not code or not name:
            flash('Code and name are required', 'danger')
        elif Course.query.filter_by(code=code).first():
            flash('Course code already exists', 'danger')
        else:
            course = Course(code=code, name=name,
                            description=request.form['description'],
                            status=request.form['status'])
            db.session.add(course)
            db.session.commit()
            flash('Course added', 'success')
        return redirect(url_for('admin.courses'))

    return render_template('admin/courses.html', courses=Course.query.all(), edit_course=None)


@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)

    if request.method == 'POST':
        code = request.form['code'].strip().upper()
        name = request.form['name'].strip()

        if not code or not name:
            flash('Code and name are required', 'danger')
            return redirect(url_for('admin.edit_course', course_id=course.id))
        # same code is allowed only if it belongs to this course
        if Course.query.filter(Course.code == code, Course.id != course.id).first():
            flash('Another course already uses this code', 'danger')
            return redirect(url_for('admin.edit_course', course_id=course.id))

        course.code = code
        course.name = name
        course.description = request.form['description']
        course.status = request.form['status']
        db.session.commit()
        flash('Course updated', 'success')
        return redirect(url_for('admin.courses'))

    return render_template('admin/courses.html', courses=Course.query.all(), edit_course=course)


@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)   # its exams are deleted too
    db.session.commit()
    flash('Course deleted', 'success')
    return redirect(url_for('admin.courses'))


# ---------------- Examinations ----------------

def fill_exam(exam):
    """Copies the form values into exam. Returns an error message, or None if everything is valid."""
    f = request.form
    try:
        exam.course_id = int(f['course_id'])
        exam.name = f['name'].strip()
        exam.exam_type = f['exam_type']
        exam.duration_min = int(f['duration_min'])
        exam.max_marks = int(f['max_marks'])
        exam.slot_creation_start = date.fromisoformat(f['slot_creation_start'])
        exam.slot_creation_end = date.fromisoformat(f['slot_creation_end'])
        exam.booking_start = date.fromisoformat(f['booking_start'])
        exam.booking_end = date.fromisoformat(f['booking_end'])
    except ValueError:
        return 'Please fill all fields correctly'

    if not exam.name:
        return 'Exam name is required'
    if exam.exam_type not in EXAM_TYPES:
        return 'Invalid exam type'
    if exam.duration_min <= 0 or exam.max_marks <= 0:
        return 'Duration and max marks must be greater than 0'
    if not (exam.slot_creation_start <= exam.slot_creation_end <= exam.booking_start <= exam.booking_end):
        return 'Dates must be in order: slot creation start <= end <= booking start <= end'
    if not db.session.get(Course, exam.course_id):
        return 'Course not found'
    return None


@admin_bp.route('/exams', methods=['GET', 'POST'])
def exams():
    if request.method == 'POST':
        exam = Examination()
        error = fill_exam(exam)
        if error:
            flash(error, 'danger')
        else:
            db.session.add(exam)
            db.session.commit()
            flash('Examination created', 'success')
        return redirect(url_for('admin.exams'))

    return render_template('admin/exams.html', exams=Examination.query.all(),
                           courses=Course.query.all(), exam_types=EXAM_TYPES,
                           statuses=EXAM_STATUSES, edit_exam=None)


@admin_bp.route('/exams/<int:exam_id>/edit', methods=['GET', 'POST'])
def edit_exam(exam_id):
    exam = Examination.query.get_or_404(exam_id)

    if request.method == 'POST':
        error = fill_exam(exam)
        if error:
            db.session.rollback()   # undo the half-filled changes
            flash(error, 'danger')
            return redirect(url_for('admin.edit_exam', exam_id=exam.id))
        db.session.commit()
        flash('Examination updated', 'success')
        return redirect(url_for('admin.exams'))

    return render_template('admin/exams.html', exams=Examination.query.all(),
                           courses=Course.query.all(), exam_types=EXAM_TYPES,
                           statuses=EXAM_STATUSES, edit_exam=exam)


@admin_bp.route('/exams/<int:exam_id>/delete', methods=['POST'])
def delete_exam(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    db.session.delete(exam)   # its rubrics and slots are deleted too
    db.session.commit()
    flash('Examination deleted', 'success')
    return redirect(url_for('admin.exams'))


# Admin opens/closes slot creation and booking by changing the exam status
@admin_bp.route('/exams/<int:exam_id>/status', methods=['POST'])
def exam_status(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    status = request.form['status']
    if status in EXAM_STATUSES:
        exam.status = status
        db.session.commit()
        flash(f'{exam.name} is now {status}', 'success')
    return redirect(url_for('admin.exams'))


@admin_bp.route('/exams/<int:exam_id>/publish', methods=['POST'])
def publish_results(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    exam.results_published = True
    db.session.commit()
    flash(f'Results published for {exam.name}', 'success')
    return redirect(url_for('admin.exams'))


# ---------------- Rubrics ----------------

def fill_rubric(rubric, exam):
    """Copies the form values into rubric. Returns an error message, or None if everything is valid."""
    f = request.form
    try:
        rubric.criterion = f['criterion'].strip()
        rubric.max_marks = int(f['max_marks'])
        rubric.weightage = float(f['weightage'])
        rubric.description = f['description'].strip()
    except ValueError:
        return 'Please fill all fields correctly'

    if not rubric.criterion:
        return 'Criterion name is required'
    if rubric.max_marks <= 0:
        return 'Max marks must be greater than 0'
    if rubric.weightage < 0 or rubric.weightage > 100:
        return 'Weightage must be between 0 and 100'

    # marks of all the other rubrics + this one must not go above the exam's max marks
    other_marks = sum(r.max_marks for r in exam.rubrics if r.id != rubric.id)
    if other_marks + rubric.max_marks > exam.max_marks:
        return f'Total rubric marks would be {other_marks + rubric.max_marks}, but exam max is {exam.max_marks}'
    return None


@admin_bp.route('/exams/<int:exam_id>/rubrics', methods=['GET', 'POST'])
def rubrics(exam_id):
    exam = Examination.query.get_or_404(exam_id)

    if request.method == 'POST':
        rubric = Rubric(exam_id=exam.id)
        error = fill_rubric(rubric, exam)
        if error:
            flash(error, 'danger')
        else:
            db.session.add(rubric)
            db.session.commit()
            flash('Rubric added', 'success')
        return redirect(url_for('admin.rubrics', exam_id=exam.id))

    total = sum(r.max_marks for r in exam.rubrics)
    examiners = User.query.filter_by(role='examiner', status='active').all()
    return render_template('admin/rubrics.html', exam=exam, total=total, edit_rubric=None,
                           examiners=examiners)


@admin_bp.route('/rubrics/<int:rubric_id>/edit', methods=['GET', 'POST'])
def edit_rubric(rubric_id):
    rubric = Rubric.query.get_or_404(rubric_id)
    exam = rubric.examination

    if request.method == 'POST':
        error = fill_rubric(rubric, exam)
        if error:
            db.session.rollback()
            flash(error, 'danger')
            return redirect(url_for('admin.edit_rubric', rubric_id=rubric.id))
        db.session.commit()
        flash('Rubric updated', 'success')
        return redirect(url_for('admin.rubrics', exam_id=exam.id))

    total = sum(r.max_marks for r in exam.rubrics)
    examiners = User.query.filter_by(role='examiner', status='active').all()
    return render_template('admin/rubrics.html', exam=exam, total=total, edit_rubric=rubric,
                           examiners=examiners)


@admin_bp.route('/rubrics/<int:rubric_id>/delete', methods=['POST'])
def delete_rubric(rubric_id):
    rubric = Rubric.query.get_or_404(rubric_id)
    exam_id = rubric.exam_id
    db.session.delete(rubric)
    db.session.commit()
    flash('Rubric deleted', 'success')
    return redirect(url_for('admin.rubrics', exam_id=exam_id))


@admin_bp.route('/exams/<int:exam_id>/assign', methods=['POST'])
def assign_examiner(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    examiner = ExaminerProfile.query.get_or_404(int(request.form['examiner_id']))
    if examiner not in exam.examiners:
        exam.examiners.append(examiner)
        db.session.commit()
        flash(f'{examiner.user.name} assigned', 'success')
    return redirect(url_for('admin.rubrics', exam_id=exam.id))


# ---------------- Examiners & Students ----------------

@admin_bp.route('/examiners')
def examiners():
    return render_template('admin/examiners.html', examiners=User.query.filter_by(role='examiner').all())


# Approve (active) or deactivate (inactive) an examiner
@admin_bp.route('/examiners/<int:user_id>/status', methods=['POST'])
def examiner_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == 'examiner' and request.form['status'] in ('active', 'inactive'):
        user.status = request.form['status']
        db.session.commit()
        flash(f'{user.name} is now {user.status}', 'success')
    return redirect(url_for('admin.examiners'))


@admin_bp.route('/students')
def students():
    return render_template('admin/students.html', students=User.query.filter_by(role='student').all())


# ---------------- Slots & Bookings ----------------

@admin_bp.route('/slots')
def slots():
    examiners = User.query.filter_by(role='examiner', status='active').all()
    return render_template('admin/slots.html', slots=Slot.query.all(), examiners=examiners)


# Change the examiner of a slot (exceptional situations)
@admin_bp.route('/slots/<int:slot_id>/examiner', methods=['POST'])
def change_examiner(slot_id):
    slot = Slot.query.get_or_404(slot_id)
    examiner = ExaminerProfile.query.get_or_404(int(request.form['examiner_id']))
    slot.examiner_id = examiner.id
    if examiner not in slot.examination.examiners:
        slot.examination.examiners.append(examiner)
    db.session.commit()
    flash(f'Slot {slot.id} examiner changed to {examiner.user.name}', 'success')
    return redirect(url_for('admin.slots'))


@admin_bp.route('/bookings')
def bookings():
    return render_template('admin/bookings.html', bookings=Booking.query.all())


# Move a booking to another slot of the same exam
@admin_bp.route('/bookings/<int:booking_id>/reschedule', methods=['POST'])
def reschedule(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    new_slot = Slot.query.get_or_404(int(request.form['slot_id']))
    old_slot = booking.slot

    if booking.status != 'Booked':
        flash('Only active bookings can be rescheduled', 'danger')
    elif new_slot.exam_id != old_slot.exam_id or new_slot.id == old_slot.id:
        flash('Choose a different slot of the same exam', 'danger')
    elif new_slot.available_seats <= 0:
        flash('That slot is full', 'danger')
    else:
        old_slot.available_seats += 1
        old_slot.status = 'Available'
        new_slot.available_seats -= 1
        if new_slot.available_seats == 0:
            new_slot.status = 'Full'
        booking.slot_id = new_slot.id
        db.session.commit()
        flash(f'Booking {booking.id} moved to slot {new_slot.id}', 'success')
    return redirect(url_for('admin.bookings'))


# ---------------- Search ----------------

@admin_bp.route('/search')
def search():
    q = request.args.get('q', '').strip().lower()
    users, exams, bookings = [], [], []
    if q:
        for u in User.query.filter(User.role != 'admin').all():
            roll_no = u.student_profile.roll_no.lower() if u.student_profile else ''
            if q in u.name.lower() or q == str(u.id) or q == roll_no:
                users.append(u)
        exams = [e for e in Examination.query.all() if q in e.name.lower() or q == str(e.id)]
        bookings = [b for b in Booking.query.all() if q == str(b.id) or q in b.student.user.name.lower()]
    return render_template('admin/search.html', q=q, users=users, exams=exams, bookings=bookings)
