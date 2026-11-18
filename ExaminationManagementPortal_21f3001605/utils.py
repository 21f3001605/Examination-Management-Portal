from datetime import date
from functools import wraps
from flask import abort
from flask_login import current_user


# Allows a route only for the given role, e.g. a student cannot open admin pages
def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if current_user.role != role:
                abort(403)
            return f(*args, **kwargs)
        return wrapper
    return decorator


# Examiners can create slots only when admin has opened slot creation AND today is inside the dates
def slot_creation_open(exam):
    return exam.status == 'Slot Creation' and exam.slot_creation_start <= date.today() <= exam.slot_creation_end


# Students can book only when admin has opened booking AND today is inside the dates
def booking_open(exam):
    return exam.status == 'Booking Open' and exam.booking_start <= date.today() <= exam.booking_end
