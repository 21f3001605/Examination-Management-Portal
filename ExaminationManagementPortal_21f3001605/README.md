# Examination Management Portal (EMP)

Flask + Jinja2 + Bootstrap + SQLite app for managing examinations with three roles: Admin, Examiner and Student.

## How to run

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

The database (`instance/emp.db`) and all tables are created automatically on first run.

## Admin login

- Email: `admin@emp.com`
- Password: `admin123`

Examiners and students register themselves. Examiners can log in only after the admin approves them.

## Demo flow

1. Admin: add a course, create an exam (dates around today), add rubrics.
2. Examiner registers, admin approves (Examiners page) and assigns them (exam > Rubrics page).
3. Admin sets the exam status to **Slot Creation** and the examiner creates slots.
4. Admin sets the status to **Booking Open** and students book slots.
5. Admin sets the status to **Closed** and the examiner evaluates students.
6. Admin clicks **Publish results** and students see their marks and remarks.
