"""
blueprints/instructor/routes.py
Instructor module: dashboard, view assigned sessions, mark attendance.
"""

from flask import render_template, request, redirect, url_for, flash, session
from datetime import date
import mysql.connector

from blueprints.instructor import instructor_bp
from utils.db import get_db
from utils.decorators import instructor_required


# ── Helper: get instructor_id for the logged-in user ─────────────────────────
def get_instructor_id(cursor):
    cursor.execute(
        'SELECT instructor_id FROM instructors WHERE user_id=%s',
        (session['user_id'],)
    )
    row = cursor.fetchone()
    return row['instructor_id'] if row else None


# ── Dashboard ─────────────────────────────────────────────────────────────────
@instructor_bp.route('/dashboard')
@instructor_required
def dashboard():
    db     = get_db()
    cursor = db.cursor(dictionary=True)

    instructor_id = get_instructor_id(cursor)

    # Classes assigned to this instructor
    cursor.execute(
        'SELECT * FROM classes WHERE instructor_id=%s AND is_active=1',
        (instructor_id,)
    )
    my_classes = cursor.fetchall()

    # Today's approved sessions
    cursor.execute('''
        SELECT b.booking_id, b.session_date, b.time_slot, b.status,
               u.full_name AS member_name, c.class_name
        FROM   bookings b
        JOIN   users    u ON b.user_id    = u.user_id
        JOIN   classes  c ON b.class_id   = c.class_id
        WHERE  c.instructor_id = %s
          AND  b.status        = 'approved'
          AND  b.session_date  = CURDATE()
        ORDER  BY b.time_slot
    ''', (instructor_id,))
    todays_sessions = cursor.fetchall()

    # Total sessions and attendance stats
    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM bookings b "
        "JOIN classes c ON b.class_id=c.class_id "
        "WHERE c.instructor_id=%s AND b.status='approved'",
        (instructor_id,)
    )
    total_sessions = cursor.fetchone()['cnt']

    cursor.execute(
        'SELECT COUNT(*) AS cnt FROM attendance WHERE instructor_id=%s AND is_present=1',
        (instructor_id,)
    )
    attended = cursor.fetchone()['cnt']

    cursor.close()
    return render_template('instructor/dashboard.html',
                           my_classes=my_classes,
                           todays_sessions=todays_sessions,
                           total_sessions=total_sessions,
                           attended=attended)


# ── All Assigned Sessions ─────────────────────────────────────────────────────
@instructor_bp.route('/sessions')
@instructor_required
def sessions():
    db     = get_db()
    cursor = db.cursor(dictionary=True)

    instructor_id = get_instructor_id(cursor)

    cursor.execute('''
        SELECT b.booking_id, b.session_date, b.time_slot, b.status,
               u.full_name AS member_name, u.email AS member_email,
               c.class_name, c.level,
               a.is_present, a.attendance_id
        FROM   bookings b
        JOIN   users    u  ON b.user_id   = u.user_id
        JOIN   classes  c  ON b.class_id  = c.class_id
        LEFT JOIN attendance a ON a.booking_id = b.booking_id
                               AND a.instructor_id = %s
        WHERE  c.instructor_id = %s
          AND  b.status        = 'approved'
        ORDER  BY b.session_date DESC, b.time_slot
    ''', (instructor_id, instructor_id))
    all_sessions = cursor.fetchall()
    cursor.close()

    return render_template('instructor/sessions.html',
                           sessions=all_sessions, today=date.today().isoformat())


# ── Mark / Update Attendance ──────────────────────────────────────────────────
@instructor_bp.route('/attendance/mark/<int:booking_id>', methods=['POST'])
@instructor_required
def mark_attendance(booking_id):
    db     = get_db()
    cursor = db.cursor(dictionary=True)

    instructor_id = get_instructor_id(cursor)
    is_present    = 1 if request.form.get('is_present') == '1' else 0
    remarks       = request.form.get('remarks', '').strip()[:255]

    # The booking must be an approved CLASS booking taught by THIS instructor
    cursor.execute('''
        SELECT b.session_date
        FROM   bookings b
        JOIN   classes  c ON b.class_id = c.class_id
        WHERE  b.booking_id    = %s
          AND  c.instructor_id = %s
          AND  b.status        = 'approved'
    ''', (booking_id, instructor_id))
    booking = cursor.fetchone()
    if not booking:
        flash('You can only mark attendance for your own approved sessions.', 'danger')
        cursor.close()
        return redirect(url_for('instructor.sessions'))

    session_date = booking['session_date']

    # Attendance cannot be recorded before the session takes place
    if session_date > date.today():
        flash('Attendance can only be marked on or after the session date.', 'warning')
        cursor.close()
        return redirect(url_for('instructor.sessions'))

    # Insert a new record or update the existing one
    cursor.execute(
        'SELECT attendance_id FROM attendance '
        'WHERE booking_id=%s AND instructor_id=%s',
        (booking_id, instructor_id)
    )
    existing = cursor.fetchone()

    try:
        if existing:
            cursor.execute(
                'UPDATE attendance SET is_present=%s, remarks=%s WHERE attendance_id=%s',
                (is_present, remarks, existing['attendance_id'])
            )
        else:
            cursor.execute(
                'INSERT INTO attendance (booking_id, instructor_id, session_date, is_present, remarks) '
                'VALUES (%s,%s,%s,%s,%s)',
                (booking_id, instructor_id, session_date, is_present, remarks)
            )
    except mysql.connector.Error as exc:   # e.g. trigger rejected the row
        db.rollback()
        flash(f'Could not save attendance: {exc.msg}', 'danger')
        cursor.close()
        return redirect(url_for('instructor.sessions'))

    db.commit()
    cursor.close()
    flash('Attendance recorded!', 'success')
    return redirect(url_for('instructor.sessions'))


# ── Attendance History ────────────────────────────────────────────────────────
@instructor_bp.route('/attendance')
@instructor_required
def attendance():
    db     = get_db()
    cursor = db.cursor(dictionary=True)

    instructor_id = get_instructor_id(cursor)

    cursor.execute('''
        SELECT a.*, u.full_name AS member_name, c.class_name
        FROM   attendance a
        JOIN   bookings   b ON a.booking_id    = b.booking_id
        JOIN   users      u ON b.user_id       = u.user_id
        JOIN   classes    c ON b.class_id      = c.class_id
        WHERE  a.instructor_id = %s
        ORDER  BY a.session_date DESC, a.marked_at DESC
    ''', (instructor_id,))
    records = cursor.fetchall()
    cursor.close()

    return render_template('instructor/attendance.html', records=records)
