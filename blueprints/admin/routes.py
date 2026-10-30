"""
blueprints/admin/routes.py
Full admin module: dashboard, classes, therapies, instructors,
bookings (approve/reject), members, feedback.
"""

from flask import render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash

from blueprints.admin import admin_bp
from utils.db import get_db
from utils.decorators import admin_required
from utils.helpers import (DAYS, LEVELS, SUGGESTED, clean_gender, clean_phone,
                           parse_int, parse_decimal, parse_time, parse_choice)


# ── Dashboard ─────────────────────────────────────────────────────────────────
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    db     = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS cnt FROM users WHERE role='member'")
    member_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM classes WHERE is_active=1")
    class_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM therapies WHERE is_active=1")
    therapy_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM bookings WHERE status='pending'")
    pending_count = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM bookings")
    total_bookings = cursor.fetchone()['cnt']

    cursor.execute("SELECT COUNT(*) AS cnt FROM instructors WHERE is_active=1")
    instructor_count = cursor.fetchone()['cnt']

    # 6 most recent bookings using the view
    cursor.execute(
        'SELECT * FROM vw_booking_details ORDER BY booked_on DESC LIMIT 6'
    )
    recent_bookings = cursor.fetchall()

    cursor.close()
    return render_template('admin/dashboard.html',
        member_count=member_count, class_count=class_count,
        therapy_count=therapy_count, pending_count=pending_count,
        total_bookings=total_bookings, instructor_count=instructor_count,
        recent_bookings=recent_bookings
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/classes')
@admin_required
def classes():
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT c.*, u.full_name AS instructor_name
        FROM   classes c
        LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
        LEFT JOIN users       u ON i.user_id        = u.user_id
        ORDER BY c.day_of_week, c.class_time
    ''')
    all_classes = cursor.fetchall()
    cursor.close()
    return render_template('admin/classes.html', classes=all_classes)


@admin_bp.route('/classes/add', methods=['GET', 'POST'])
@admin_required
def add_class():
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    instructors = _active_instructors(cursor)

    if request.method == 'POST':
        data, errors = _class_from_form(request.form)
        if errors:
            for err in errors:
                flash(err, 'danger')
            cursor.close()
            return render_template('admin/class_form.html', action='Add',
                                   cls=request.form, instructors=instructors)
        cursor.execute('''
            INSERT INTO classes
            (class_name, description, instructor_id, day_of_week, class_time,
             duration_minutes, total_seats, available_seats, fee, level, suggested_for)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ''', (data['class_name'], data['description'], data['instructor_id'],
              data['day_of_week'], data['class_time'], data['duration_minutes'],
              data['total_seats'], data['total_seats'],
              data['fee'], data['level'], data['suggested_for']))
        db.commit()
        cursor.close()
        flash('Yoga class added successfully!', 'success')
        return redirect(url_for('admin.classes'))

    cursor.close()
    return render_template('admin/class_form.html',
                           action='Add', cls={}, instructors=instructors)


@admin_bp.route('/classes/edit/<int:class_id>', methods=['GET', 'POST'])
@admin_required
def edit_class(class_id):
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    instructors = _active_instructors(cursor)

    if request.method == 'POST':
        data, errors = _class_from_form(request.form)
        if errors:
            for err in errors:
                flash(err, 'danger')
            cursor.close()
            return render_template('admin/class_form.html', action='Edit',
                                   cls=request.form, instructors=instructors)
        cursor.execute('''
            UPDATE classes SET
                class_name=%s, description=%s, instructor_id=%s, day_of_week=%s,
                class_time=%s, duration_minutes=%s, total_seats=%s, fee=%s,
                level=%s, suggested_for=%s
            WHERE class_id=%s
        ''', (data['class_name'], data['description'], data['instructor_id'],
              data['day_of_week'], data['class_time'], data['duration_minutes'],
              data['total_seats'], data['fee'], data['level'],
              data['suggested_for'], class_id))
        db.commit()
        cursor.close()
        flash('Class updated successfully!', 'success')
        return redirect(url_for('admin.classes'))

    cursor.execute('SELECT * FROM classes WHERE class_id=%s', (class_id,))
    cls = cursor.fetchone()
    cursor.close()

    if not cls:
        flash('Class not found.', 'danger')
        return redirect(url_for('admin.classes'))

    return render_template('admin/class_form.html',
                           action='Edit', cls=cls, instructors=instructors)


def _active_instructors(cursor):
    """Instructors shown in the class form dropdown."""
    cursor.execute(
        'SELECT i.instructor_id, u.full_name FROM instructors i '
        'JOIN users u ON i.user_id=u.user_id WHERE i.is_active=1'
    )
    return cursor.fetchall()


@admin_bp.route('/classes/delete/<int:class_id>', methods=['POST'])
@admin_required
def delete_class(class_id):
    db     = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE classes SET is_active=0 WHERE class_id=%s', (class_id,))
    db.commit()
    cursor.close()
    flash('Class deactivated.', 'info')
    return redirect(url_for('admin.classes'))


def _class_from_form(form):
    """Validate and coerce class fields. Returns (data, errors)."""
    errors = []
    name = form.get('class_name', '').strip()
    if not name or len(name) > 150:
        errors.append('Class name is required (max 150 characters).')

    instructor_id = form.get('instructor_id') or None
    if instructor_id is not None:
        instructor_id = parse_int(instructor_id, 'Instructor', errors, 1, 10**9)

    data = {
        'class_name':       name,
        'description':      form.get('description', '').strip(),
        'instructor_id':    instructor_id,
        'day_of_week':      parse_choice(form.get('day_of_week', ''), DAYS, 'day of week', errors),
        'class_time':       parse_time(form.get('class_time', ''), 'Class time', errors),
        'duration_minutes': parse_int(form.get('duration_minutes'), 'Duration (minutes)', errors, 10, 480),
        'total_seats':      parse_int(form.get('total_seats'), 'Total seats', errors, 1, 500),
        'fee':              parse_decimal(form.get('fee'), 'Fee', errors, 0, 100000),
        'level':            parse_choice(form.get('level', 'All Levels'), LEVELS, 'level', errors),
        'suggested_for':    parse_choice(form.get('suggested_for', 'All'), SUGGESTED, 'BMI category', errors),
    }
    return data, errors


# ═══════════════════════════════════════════════════════════════════════════════
# THERAPIES
# ═══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/therapies')
@admin_required
def therapies():
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM therapies WHERE is_active=1 ORDER BY therapy_name'
    )
    all_therapies = cursor.fetchall()
    cursor.close()
    return render_template('admin/therapies.html', therapies=all_therapies)


@admin_bp.route('/therapies/add', methods=['GET', 'POST'])
@admin_required
def add_therapy():
    if request.method == 'POST':
        data, errors = _therapy_from_form(request.form)
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/therapy_form.html',
                                   action='Add', therapy=request.form)
        db     = get_db()
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO therapies (therapy_name, description, duration_minutes, fee) '
            'VALUES (%s,%s,%s,%s)',
            (data['therapy_name'], data['description'],
             data['duration_minutes'], data['fee'])
        )
        db.commit()
        cursor.close()
        flash('Therapy service added!', 'success')
        return redirect(url_for('admin.therapies'))
    return render_template('admin/therapy_form.html', action='Add', therapy={})


@admin_bp.route('/therapies/edit/<int:therapy_id>', methods=['GET', 'POST'])
@admin_required
def edit_therapy(therapy_id):
    db     = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        data, errors = _therapy_from_form(request.form)
        if errors:
            for err in errors:
                flash(err, 'danger')
            cursor.close()
            return render_template('admin/therapy_form.html',
                                   action='Edit', therapy=request.form)
        cursor.execute(
            'UPDATE therapies SET therapy_name=%s, description=%s, '
            'duration_minutes=%s, fee=%s WHERE therapy_id=%s',
            (data['therapy_name'], data['description'],
             data['duration_minutes'], data['fee'], therapy_id)
        )
        db.commit()
        cursor.close()
        flash('Therapy updated!', 'success')
        return redirect(url_for('admin.therapies'))

    cursor.execute('SELECT * FROM therapies WHERE therapy_id=%s', (therapy_id,))
    therapy = cursor.fetchone()
    cursor.close()
    if not therapy:
        flash('Therapy not found.', 'danger')
        return redirect(url_for('admin.therapies'))
    return render_template('admin/therapy_form.html',
                           action='Edit', therapy=therapy)


@admin_bp.route('/therapies/delete/<int:therapy_id>', methods=['POST'])
@admin_required
def delete_therapy(therapy_id):
    db     = get_db()
    cursor = db.cursor()
    cursor.execute('UPDATE therapies SET is_active=0 WHERE therapy_id=%s', (therapy_id,))
    db.commit()
    cursor.close()
    flash('Therapy deactivated.', 'info')
    return redirect(url_for('admin.therapies'))


def _therapy_from_form(form):
    """Validate and coerce therapy fields. Returns (data, errors)."""
    errors = []
    name = form.get('therapy_name', '').strip()
    if not name or len(name) > 150:
        errors.append('Therapy name is required (max 150 characters).')
    data = {
        'therapy_name':     name,
        'description':      form.get('description', '').strip(),
        'duration_minutes': parse_int(form.get('duration_minutes'), 'Duration (minutes)', errors, 10, 480),
        'fee':              parse_decimal(form.get('fee'), 'Fee', errors, 0, 100000),
    }
    return data, errors


# ═══════════════════════════════════════════════════════════════════════════════
# INSTRUCTORS
# ═══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/instructors')
@admin_required
def instructors():
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT i.*, u.full_name, u.email, u.phone, u.gender
        FROM   instructors i
        JOIN   users       u ON i.user_id = u.user_id
        WHERE  i.is_active = 1
        ORDER  BY u.full_name
    ''')
    all_instructors = cursor.fetchall()
    cursor.close()
    return render_template('admin/instructors.html',
                           instructors=all_instructors)


@admin_bp.route('/instructors/add', methods=['GET', 'POST'])
@admin_required
def add_instructor():
    if request.method == 'POST':
        errors = []
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        password  = request.form.get('password', '')
        phone     = clean_phone(request.form.get('phone', ''), errors)
        gender    = clean_gender(request.form.get('gender', ''))
        experience = parse_int(request.form.get('experience_years', 0),
                               'Experience (years)', errors, 0, 70)

        if not full_name or len(full_name) > 100:
            errors.append('Full name is required (max 100 characters).')
        if not email or '@' not in email or len(email) > 150:
            errors.append('A valid email address is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long.')

        form = request.form
        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('admin/instructor_form.html',
                                   action='Add', instructor=form)

        specialization = form.get('specialization', '').strip()[:200]
        bio            = form.get('bio', '').strip()
        certification  = form.get('certification', '').strip()[:200]

        db     = get_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute('SELECT user_id FROM users WHERE email=%s', (email,))
        if cursor.fetchone():
            flash('Email already registered.', 'warning')
            cursor.close()
            return render_template('admin/instructor_form.html',
                                   action='Add', instructor=form)

        hashed = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (full_name, email, password_hash, role, phone, gender) '
            'VALUES (%s,%s,%s,%s,%s,%s)',
            (full_name, email, hashed, 'instructor', phone, gender)
        )
        new_user_id = cursor.lastrowid

        cursor.execute(
            'INSERT INTO instructors (user_id, specialization, experience_years, bio, certification) '
            'VALUES (%s,%s,%s,%s,%s)',
            (new_user_id, specialization, experience, bio, certification)
        )
        db.commit()
        cursor.close()
        flash(f'Instructor {full_name} added!', 'success')
        return redirect(url_for('admin.instructors'))

    return render_template('admin/instructor_form.html',
                           action='Add', instructor={})


@admin_bp.route('/instructors/edit/<int:instructor_id>', methods=['GET', 'POST'])
@admin_required
def edit_instructor(instructor_id):
    db     = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        errors = []
        full_name  = request.form.get('full_name', '').strip()
        phone      = clean_phone(request.form.get('phone', ''), errors)
        gender     = clean_gender(request.form.get('gender', ''))
        experience = parse_int(request.form.get('experience_years', 0),
                               'Experience (years)', errors, 0, 70)
        if not full_name or len(full_name) > 100:
            errors.append('Full name is required (max 100 characters).')
        if errors:
            for err in errors:
                flash(err, 'danger')
            cursor.close()
            data = request.form.to_dict()
            data['instructor_id'] = instructor_id
            return render_template('admin/instructor_form.html',
                                   action='Edit', instructor=data)

        specialization = request.form.get('specialization', '').strip()[:200]
        bio            = request.form.get('bio', '').strip()
        certification  = request.form.get('certification', '').strip()[:200]

        cursor.execute(
            'SELECT user_id FROM instructors WHERE instructor_id=%s', (instructor_id,)
        )
        row = cursor.fetchone()
        if row:
            cursor.execute(
                'UPDATE users SET full_name=%s, phone=%s, gender=%s WHERE user_id=%s',
                (full_name, phone, gender, row['user_id'])
            )
            cursor.execute(
                'UPDATE instructors SET specialization=%s, experience_years=%s, '
                'bio=%s, certification=%s WHERE instructor_id=%s',
                (specialization, experience, bio, certification, instructor_id)
            )
            db.commit()
            flash('Instructor updated!', 'success')
        else:
            flash('Instructor not found.', 'danger')
        cursor.close()
        return redirect(url_for('admin.instructors'))

    cursor.execute('''
        SELECT i.*, u.full_name, u.email, u.phone, u.gender
        FROM   instructors i
        JOIN   users       u ON i.user_id=u.user_id
        WHERE  i.instructor_id=%s
    ''', (instructor_id,))
    instructor = cursor.fetchone()
    cursor.close()
    if not instructor:
        flash('Instructor not found.', 'danger')
        return redirect(url_for('admin.instructors'))
    return render_template('admin/instructor_form.html',
                           action='Edit', instructor=instructor)


@admin_bp.route('/instructors/delete/<int:instructor_id>', methods=['POST'])
@admin_required
def delete_instructor(instructor_id):
    """Deactivate the instructor profile AND their login, and unassign their classes."""
    db     = get_db()
    cursor = db.cursor()
    cursor.execute(
        'UPDATE users u JOIN instructors i ON i.user_id = u.user_id '
        'SET u.is_active = 0, i.is_active = 0 WHERE i.instructor_id = %s',
        (instructor_id,)
    )
    cursor.execute(
        'UPDATE classes SET instructor_id = NULL WHERE instructor_id = %s',
        (instructor_id,)
    )
    db.commit()
    cursor.close()
    flash('Instructor deactivated. Their classes are now unassigned.', 'info')
    return redirect(url_for('admin.instructors'))


# ═══════════════════════════════════════════════════════════════════════════════
# BOOKINGS
# ═══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/bookings')
@admin_required
def bookings():
    status_filter = request.args.get('status', 'all')
    db     = get_db()
    cursor = db.cursor(dictionary=True)

    if status_filter == 'all':
        cursor.execute(
            'SELECT * FROM vw_booking_details ORDER BY booked_on DESC'
        )
    else:
        cursor.execute(
            'SELECT * FROM vw_booking_details WHERE status=%s ORDER BY booked_on DESC',
            (status_filter,)
        )
    all_bookings = cursor.fetchall()
    cursor.close()
    return render_template('admin/bookings.html',
                           bookings=all_bookings,
                           status_filter=status_filter)


@admin_bp.route('/bookings/update/<int:booking_id>/<action>', methods=['POST'])
@admin_required
def update_booking(booking_id, action):
    """Approve or reject a booking (only valid status transitions are allowed)."""
    if action == 'approve':
        new_status, allowed_from = 'approved', ('pending',)
    elif action == 'reject':
        new_status, allowed_from = 'rejected', ('pending', 'approved')
    else:
        flash('Invalid action.', 'danger')
        return redirect(url_for('admin.bookings'))

    db     = get_db()
    cursor = db.cursor()
    cursor.execute(
        'UPDATE bookings SET status=%s '
        'WHERE booking_id=%s AND status IN (' + ','.join(['%s'] * len(allowed_from)) + ')',
        (new_status, booking_id) + allowed_from
    )
    changed = cursor.rowcount
    db.commit()
    cursor.close()

    if changed:
        flash(f'Booking #{booking_id} {new_status}.', 'success')
    else:
        flash(f'Booking #{booking_id} cannot be {new_status} '
              '(it may already be cancelled, rejected or processed).', 'warning')
    return redirect(url_for('admin.bookings'))


# ═══════════════════════════════════════════════════════════════════════════════
# MEMBERS
# ═══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/members')
@admin_required
def members():
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE role='member' ORDER BY created_at DESC"
    )
    all_members = cursor.fetchall()
    cursor.close()
    return render_template('admin/members.html', members=all_members)


# ═══════════════════════════════════════════════════════════════════════════════
# FEEDBACK
# ═══════════════════════════════════════════════════════════════════════════════

@admin_bp.route('/feedback')
@admin_required
def feedback():
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT f.*, u.full_name AS member_name,
               c.class_name, t.therapy_name
        FROM   feedback f
        JOIN   users    u ON f.user_id    = u.user_id
        LEFT JOIN classes   c ON f.class_id   = c.class_id
        LEFT JOIN therapies t ON f.therapy_id = t.therapy_id
        ORDER  BY f.submitted_at DESC
    ''')
    all_feedback = cursor.fetchall()
    cursor.close()
    return render_template('admin/feedback.html', feedback=all_feedback)
