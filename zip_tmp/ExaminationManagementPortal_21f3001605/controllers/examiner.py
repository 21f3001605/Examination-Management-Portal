from datetime import date, time
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from utils import role_required, slot_creation_open
from models import db, Examination, Slot, Booking, Evaluation, EvaluationScore

examiner_bp = Blueprint('examiner', __name__, url_prefix='/examiner')


@examiner_bp.before_request
@login_required
@role_required('examiner')
def protect():
    pass


def my_profile():
    return current_user.examiner_profile


def my_slot(slot_id):
    """Returns the slot only if it belongs to the logged-in examiner."""
    slot = Slot.query.get_or_404(slot_id)
    if slot.examiner_id != my_profile().id:
        abort(403)
    return slot


@examiner_bp.route('/dashboard')
def dashboard():
    me = my_profile()
    booked = [b for s in me.slots for b in s.bookings if b.status != 'Cancelled']
    pending = [b for b in booked if b.status == 'Booked']
    return render_template('examiner/dashboard.html', exams=me.assigned_exams, slots=me.slots,
                           booked_count=len(booked), pending=pending, slot_creation_open=slot_creation_open)


@examiner_bp.route('/slots')
def slots():
    return render_template('examiner/slots.html', slots=my_profile().slots)


def fill_slot(slot):
    """Copies the form values into slot. Returns an error message, or None if everything is valid."""
    f = request.form
    try:
        slot.date = date.fromisoformat(f['date'])
        slot.start_time = time.fromisoformat(f['start_time'])
        slot.end_time = time.fromisoformat(f['end_time'])
        capacity = int(f['capacity'])
    except ValueError:
        return 'Please fill all fields correctly'

    if slot.end_time <= slot.start_time:
        return 'End time must be after start time'
    if capacity < 1:
        return 'Capacity must be at least 1'

    booked = len([b for b in slot.bookings if b.status == 'Booked'])
    if capacity < booked:
        return f'{booked} students already booked, capacity cannot be less'
    slot.capacity = capacity
    slot.available_seats = capacity - booked
    slot.status = 'Full' if slot.available_seats == 0 else 'Available'
    return None


@examiner_bp.route('/exams/<int:exam_id>/slots/new', methods=['GET', 'POST'])
def create_slot(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    if exam not in my_profile().assigned_exams:
        abort(403)
    if not slot_creation_open(exam):
        flash('Slot creation is not open for this exam', 'danger')
        return redirect(url_for('examiner.dashboard'))

    if request.method == 'POST':
        slot = Slot(exam_id=exam.id, examiner_id=my_profile().id)
        error = fill_slot(slot)
        if error:
            flash(error, 'danger')
            return redirect(url_for('examiner.create_slot', exam_id=exam.id))
        db.session.add(slot)
        db.session.commit()
        flash('Slot created', 'success')
        return redirect(url_for('examiner.slots'))

    return render_template('examiner/slot_form.html', exam=exam, slot=None)


# Slots can be changed only before booking starts (exam still in 'Slot Creation')
@examiner_bp.route('/slots/<int:slot_id>/edit', methods=['GET', 'POST'])
def edit_slot(slot_id):
    slot = my_slot(slot_id)
    if slot.examination.status != 'Slot Creation':
        flash('Slots cannot be changed after booking has started', 'danger')
        return redirect(url_for('examiner.slots'))

    if request.method == 'POST':
        error = fill_slot(slot)
        if error:
            db.session.rollback()
            flash(error, 'danger')
            return redirect(url_for('examiner.edit_slot', slot_id=slot.id))
        db.session.commit()
        flash('Slot updated', 'success')
        return redirect(url_for('examiner.slots'))

    return render_template('examiner/slot_form.html', exam=slot.examination, slot=slot)


@examiner_bp.route('/slots/<int:slot_id>/delete', methods=['POST'])
def delete_slot(slot_id):
    slot = my_slot(slot_id)
    if slot.examination.status != 'Slot Creation':
        flash('Slots cannot be removed after booking has started', 'danger')
    else:
        db.session.delete(slot)
        db.session.commit()
        flash('Slot deleted', 'success')
    return redirect(url_for('examiner.slots'))


@examiner_bp.route('/slots/<int:slot_id>/students')
def slot_students(slot_id):
    slot = my_slot(slot_id)
    bookings = [b for b in slot.bookings if b.status != 'Cancelled']
    return render_template('examiner/students.html', slot=slot, bookings=bookings)


# Examiner can evaluate only students booked into their own slots
@examiner_bp.route('/bookings/<int:booking_id>/evaluate', methods=['GET', 'POST'])
def evaluate(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    my_slot(booking.slot_id)   # 403 if not my slot
    exam = booking.slot.examination
    if booking.status == 'Cancelled':
        flash('This booking was cancelled', 'danger')
        return redirect(url_for('examiner.slot_students', slot_id=booking.slot_id))

    if request.method == 'POST':
        # first check all the marks
        marks = {}
        for r in exam.rubrics:
            try:
                marks[r.id] = float(request.form[f'rubric_{r.id}'])
            except ValueError:
                flash('Enter marks for every criterion', 'danger')
                return redirect(url_for('examiner.evaluate', booking_id=booking.id))
            if marks[r.id] < 0 or marks[r.id] > r.max_marks:
                flash(f'{r.criterion}: marks must be between 0 and {r.max_marks}', 'danger')
                return redirect(url_for('examiner.evaluate', booking_id=booking.id))

        # then save them (an existing evaluation is overwritten)
        evaluation = booking.evaluation or Evaluation(booking_id=booking.id, examiner_id=my_profile().id)
        evaluation.scores = [EvaluationScore(rubric_id=rid, marks=m) for rid, m in marks.items()]
        evaluation.total_marks = sum(marks.values())
        evaluation.remarks = request.form['remarks'].strip()
        booking.status = 'Completed'
        db.session.add(evaluation)
        db.session.commit()
        flash(f'Evaluation saved for {booking.student.user.name}', 'success')
        return redirect(url_for('examiner.slot_students', slot_id=booking.slot_id))

    old_marks = {}
    if booking.evaluation:
        old_marks = {s.rubric_id: s.marks for s in booking.evaluation.scores}
    return render_template('examiner/evaluate.html', booking=booking, exam=exam, old_marks=old_marks)
