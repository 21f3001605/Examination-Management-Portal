from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, ExaminerProfile, StudentProfile

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for(current_user.role + '.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        if user.status == 'pending':
            flash('Your account is waiting for admin approval', 'warning')
            return redirect(url_for('auth.login'))
        if user.status == 'inactive':
            flash('Your account has been deactivated', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user)
        return redirect(url_for(user.role + '.dashboard'))

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        roll_no = request.form['roll_no'].strip()

        # nobody can register as admin
        if role not in ('student', 'examiner'):
            flash('Invalid role', 'danger')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))
        if role == 'student' and not roll_no:
            flash('Roll number is required for students', 'danger')
            return redirect(url_for('auth.register'))
        if role == 'student' and StudentProfile.query.filter_by(roll_no=roll_no).first():
            flash('Roll number already registered', 'danger')
            return redirect(url_for('auth.register'))

        user = User(name=name, email=email, role=role,
                    password_hash=generate_password_hash(password))

        if role == 'student':
            user.status = 'active'
            user.student_profile = StudentProfile(roll_no=roll_no)
            flash('Registered! Please log in.', 'success')
        else:
            user.status = 'pending'   # examiner waits for admin approval
            user.examiner_profile = ExaminerProfile(department=request.form['department'],
                                                    phone=request.form['phone'])
            flash('Registered! Wait for admin approval before logging in.', 'info')

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
