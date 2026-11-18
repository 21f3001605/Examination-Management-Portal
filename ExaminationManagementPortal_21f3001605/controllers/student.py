from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from utils import role_required, booking_open
from models import db, Examination, Slot, Booking

student_bp = Blueprint('student', __name__, url_prefix='/student')

EXAM_TYPES = ['Viva', 'Practical', 'Project Demo', 'Assessment']


@student_bp.before_request
@login_required
@role_required('student')
def protect():
    pass


def my_profile():
    return current_user.student_profile


def has_booked(exam):
    """True if the student already has an active (not cancelled) booking for this exam."""
    for b in my_profile().bookings:
        if b.slot.exam_id == exam.id and b.status != 'Cancelled':
            return True
    return False


@student_bp.route('/dashboard')
def dashboard():
    my_bookings = my_profile().bookings
    open_exams = [e for e in Examination.query.all() if booking_open(e)]
    open_slots = [s for e in open_exams for s in e.slots if s.status == 'Available']
    upcoming = [b for b in my_bookings if b.status == 'Booked' and b.slot.date >= date.today()]
    results = [b for b in my_bookings if b.evaluation and b.slot.examination.results_published]
    return render_template('student/dashboard.html', open_exams=open_exams, open_slots=open_slots,
                           upcoming=upcoming, results=results)


# Search by name / course code and filter by exam type
@student_bp.route('/exams')
def exams():
    q = request.args.get('q', '').strip().lower()
    exam_type = request.args.get('type', '')
    exams = []
    for e in Examination.query.filter(Examination.status != 'Draft').all():
        if q and q not in e.name.lower() and q not in e.course.code.lower():
            continue
        if exam_type and e.exam_type != exam_type:
            continue
        exams.append(e)
    return render_template('student/exams.html', exams=exams, q=q, exam_type=exam_type,
                           exam_types=EXAM_TYPES, booking_open=booking_open)


@student_bp.route('/exams/<int:exam_id>/book')
def book(exam_id):
    exam = Examination.query.get_or_404(exam_id)
    return render_template('student/book.html', exam=exam, is_open=booking_open(exam),
                           already_booked=has_booked(exam))


@student_bp.route('/slots/<int:slot_id>/book', methods=['POST'])
def book_slot(slot_id):
    slot = Slot.query.get_or_404(slot_id)
    exam = slot.examination

    if not booking_open(exam):
        flash('Booking is not open for this exam', 'danger')
    elif has_booked(exam):
        flash('You have already booked a slot for this exam', 'danger')
    elif slot.available_seats <= 0:
        flash('This slot is full', 'danger')
    else:
        db.session.add(Booking(student_id=my_profile().id, slot_id=slot.id))
        slot.available_seats -= 1
        if slot.available_seats == 0:
            slot.status = 'Full'   # close the slot automatically
        db.session.commit()
        flash('Slot booked', 'success')
        return redirect(url_for('student.bookings'))
    return redirect(url_for('student.book', exam_id=exam.id))


@student_bp.route('/bookings')
def bookings():
    return render_template('student/bookings.html', bookings=my_profile().bookings, today=date.today())


# Cancel only before the booking deadline. The booking is kept with status 'Cancelled' (history).
@student_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
def cancel(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.student_id != my_profile().id:
        abort(403)

    if booking.status != 'Booked':
        flash('This booking cannot be cancelled', 'danger')
    elif date.today() > booking.slot.examination.booking_end:
        flash('Booking deadline has passed', 'danger')
    else:
        booking.status = 'Cancelled'
        booking.slot.available_seats += 1
        booking.slot.status = 'Available'
        db.session.commit()
        flash('Booking cancelled', 'success')
    return redirect(url_for('student.bookings'))


@student_bp.route('/results')
def results():
    results = [b for b in my_profile().bookings if b.evaluation and b.slot.examination.results_published]
    return render_template('student/results.html', results=results)


@student_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash('Name is required', 'danger')
            return redirect(url_for('student.profile'))
        current_user.name = name
        if request.form['password']:
            current_user.password_hash = generate_password_hash(request.form['password'])
        db.session.commit()
        flash('Profile updated', 'success')
        return redirect(url_for('student.profile'))
    return render_template('student/profile.html')
