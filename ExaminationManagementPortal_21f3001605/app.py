from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

from models import db, User
from controllers.auth import auth_bp
from controllers.admin import admin_bp
from controllers.examiner import examiner_bp
from controllers.student import student_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'any-secret-string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emp.db'

db.init_app(app)

# Flask-Login remembers who is logged in. After login it stores the user id in the
# session and calls load_user on every request to get the current user back.
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(examiner_bp)
app.register_blueprint(student_bp)

# Create all tables and the admin account (admin cannot register)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        admin = User(name='Admin', email='admin@emp.com',
                     password_hash=generate_password_hash('admin123'),
                     role='admin', status='active')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
