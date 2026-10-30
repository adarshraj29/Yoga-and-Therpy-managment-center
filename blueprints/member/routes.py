"""
blueprints/member/routes.py
Member module: dashboard, browse classes & therapies, book sessions,
my bookings (with cancel), submit feedback, BMI calculator, Asana library.
"""

from flask import render_template, request, redirect, url_for, flash, session
from datetime import date

from blueprints.member import member_bp
from utils.db import get_db
from utils.decorators import member_required
from utils.bmi import calculate_bmi, get_bmi_advice, ASANA_LIBRARY
from utils.helpers import next_session_date, weekday_name, parse_time

# Time slots offered for therapy sessions (classes always use their own fixed time)
THERAPY_SLOTS = [
    ('06:00:00', '6:00 AM - Early Morning'),
    ('07:00:00', '7:00 AM - Morning'),
    ('08:00:00', '8:00 AM - Morning'),
    ('09:00:00', '9:00 AM - Mid-Morning'),
    ('10:00:00', '10:00 AM - Late Morning'),
    ('11:00:00', '11:00 AM - Pre-Noon'),
    ('16:00:00', '4:00 PM - Late Afternoon'),
    ('17:00:00', '5:00 PM - Evening'),
    ('18:00:00', '6:00 PM - Evening'),
    ('19:00:00', '7:00 PM - Night'),
]


# ── Dashboard ─────────────────────────────────────────────────────────────────
@member_bp.route('/dashboard')
@member_required
def dashboard():
    user_id = session['user_id']
    db      = get_db()
    cursor  = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM bookings WHERE user_id=%s AND status='pending'",
        (user_id,)
    )
    pending = cursor.fetchone()['cnt']

    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM bookings WHERE user_id=%s AND status='approved'",
        (user_id,)
    )
    approved = cursor.fetchone()['cnt']

    cursor.execute(
        "SELECT COUNT(*) AS cnt FROM bookings WHERE user_id=%s",
        (user_id,)
    )
    total = cursor.fetchone()['cnt']

    # Upcoming 3 approved bookings
    cursor.execute('''
        SELECT b.booking_id, b.session_date, b.time_slot, b.booking_type,
               c.class_name, t.therapy_name
        FROM   bookings b
        LEFT JOIN classes   c ON b.class_id   = c.class_id
        LEFT JOIN therapies t ON b.therapy_id = t.therapy_id
        WHERE  b.user_id=%s AND b.status='approved' AND b.session_date >= CURDATE()
        ORDER  BY b.session_date ASC LIMIT 3
    ''', (user_id,))
    upcoming = cursor.fetchall()

    cursor.close()
    return render_template('member/dashboard.html',
                           pending=pending, approved=approved,
                           total=total, upcoming=upcoming)


# ── Browse Classes ────────────────────────────────────────────────────────────
@member_bp.route('/classes')
@member_required
def classes():
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT c.*, u.full_name AS instructor_name
        FROM   classes c
        LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
        LEFT JOIN users       u ON i.user_id        = u.user_id
        WHERE  c.is_active = 1
        ORDER  BY c.day_of_week, c.class_time
    ''')
    all_classes = cursor.fetchall()

    # Seats are tracked per session date: show the NEXT session's availability
    for cls in all_classes:
        next_date = next_session_date(cls['day_of_week'])
        cursor.execute('SELECT fn_available_seats(%s, %s) AS seats',
                       (cls['class_id'], next_date))
        cls['next_date']  = next_date
        cls['seats_left'] = cursor.fetchone()['seats']

    cursor.close()
    return render_template('member/classes.html', classes=all_classes)


# ── Browse Therapies ──────────────────────────────────────────────────────────
@member_bp.route('/therapies')
@member_required
def therapies():
    db     = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM therapies WHERE is_active=1 ORDER BY therapy_name'
    )
    all_therapies = cursor.fetchall()
    cursor.close()
    return render_template('member/therapies.html', therapies=all_therapies)


# ── Book a Session ────────────────────────────────────────────────────────────
def _render_book(cursor, item, booking_type):
    """Render the booking form (adds next-session info for classes)."""
    extra = {}
    if booking_type == 'class':
        next_date = next_session_date(item['day_of_week'])
        cursor.execute('SELECT fn_available_seats(%s, %s) AS seats',
                       (item['class_id'], next_date))
        extra = {
            'next_date':  next_date,
            'seats_left': cursor.fetchone()['seats'],
            # JavaScript getDay(): Sunday=0 ... Saturday=6
            'js_weekday': (next_date.weekday() + 1) % 7,
        }
    return render_template('member/book.html', item=item,
                           booking_type=booking_type,
                           today=date.today().isoformat(),
                           slots=THERAPY_SLOTS, **extra)


@member_bp.route('/book/<booking_type>/<int:item_id>', methods=['GET', 'POST'])
@member_required
def book(booking_type, item_id):
    """
    booking_type: 'class' or 'therapy'
    item_id     : class_id or therapy_id
    """
    if booking_type not in ('class', 'therapy'):
        flash('Invalid booking type.', 'danger')
        return redirect(url_for('member.classes'))

    db     = get_db()
    cursor = db.cursor(dictionary=True)

    if booking_type == 'class':
        cursor.execute(
            'SELECT * FROM classes WHERE class_id=%s AND is_active=1', (item_id,)
        )
    else:
        cursor.execute(
            'SELECT * FROM therapies WHERE therapy_id=%s AND is_active=1', (item_id,)
        )
    item = cursor.fetchone()

    if not item:
        flash('The selected session is not available.', 'warning')
        cursor.close()
        return redirect(url_for('member.classes'))

    if request.method == 'POST':
        session_date = request.form.get('session_date', '')

        # --- validate the date ---
        try:
            chosen = date.fromisoformat(session_date)
        except ValueError:
            flash('Please select a valid date.', 'danger')
            page = _render_book(cursor, item, booking_type)
            cursor.close()
            return page
        if chosen < date.today():
            flash('Please choose a future date.', 'warning')
            page = _render_book(cursor, item, booking_type)
            cursor.close()
            return page

        # --- decide the time slot ---
        errors = []
        if booking_type == 'class':
            # A class runs on one weekday at one fixed time
            if weekday_name(chosen) != item['day_of_week']:
                flash(f"{item['class_name']} runs on {item['day_of_week']}s only. "
                      f"Please pick a {item['day_of_week']}.", 'warning')
                page = _render_book(cursor, item, booking_type)
                cursor.close()
                return page
            time_slot = parse_time(str(item['class_time']), 'Class time', errors)
        else:
            time_slot = request.form.get('time_slot', '')
            if time_slot not in dict(THERAPY_SLOTS):
                flash('Please select a valid time slot.', 'warning')
                page = _render_book(cursor, item, booking_type)
                cursor.close()
                return page

        user_id    = session['user_id']
        class_id   = item_id if booking_type == 'class'   else None
        therapy_id = item_id if booking_type == 'therapy' else None

        # Call stored procedure sp_book_session (seat check + duplicate check)
        args = (user_id, booking_type, class_id, therapy_id,
                chosen.isoformat(), time_slot, 0)
        cursor.callproc('sp_book_session', args)

        # Read the OUT param (index 6 -> @_sp_book_session_6)
        cursor.execute('SELECT @_sp_book_session_6')
        result_code = list(cursor.fetchone().values())[0]
        db.commit()
        cursor.close()

        if result_code == 0:
            flash('Booking submitted! Awaiting admin approval.', 'success')
        elif result_code == 1:
            flash('Sorry, no seats are available for that date.', 'warning')
        elif result_code == 2:
            flash('You have already booked this session on that date.', 'info')
        else:
            flash('Something went wrong. Please try again.', 'danger')
        return redirect(url_for('member.my_bookings'))

    page = _render_book(cursor, item, booking_type)
    cursor.close()
    return page


# ── My Bookings ───────────────────────────────────────────────────────────────
@member_bp.route('/my-bookings')
@member_required
def my_bookings():
    user_id = session['user_id']
    db      = get_db()
    cursor  = db.cursor(dictionary=True)
    cursor.execute('''
        SELECT b.*, c.class_name, t.therapy_name
        FROM   bookings b
        LEFT JOIN classes   c ON b.class_id   = c.class_id
        LEFT JOIN therapies t ON b.therapy_id = t.therapy_id
        WHERE  b.user_id = %s
        ORDER  BY b.session_date DESC, b.created_at DESC
    ''', (user_id,))
    bookings = cursor.fetchall()
    cursor.close()
    return render_template('member/my_bookings.html', bookings=bookings)


# ── Cancel a Booking ──────────────────────────────────────────────────────────
@member_bp.route('/cancel-booking/<int:booking_id>', methods=['POST'])
@member_required
def cancel_booking(booking_id):
    user_id = session['user_id']
    db      = get_db()
    cursor  = db.cursor(dictionary=True)

    # Call stored procedure sp_cancel_booking
    cursor.callproc('sp_cancel_booking', (booking_id, user_id, 0))
    cursor.execute('SELECT @_sp_cancel_booking_2')
    result_row  = cursor.fetchone()
    result_code = list(result_row.values())[0]
    db.commit()
    cursor.close()

    if result_code == 0:
        flash('Booking cancelled successfully.', 'info')
    else:
        flash('Unable to cancel this booking.', 'danger')

    return redirect(url_for('member.my_bookings'))


# ── Submit Feedback ───────────────────────────────────────────────────────────
@member_bp.route('/feedback', methods=['GET', 'POST'])
@member_required
def feedback():
    user_id = session['user_id']
    db      = get_db()
    cursor  = db.cursor(dictionary=True)

    if request.method == 'POST':
        booking_type = request.form.get('booking_type', '')
        comments     = request.form.get('comments', '').strip()[:1000]

        try:
            rating = int(request.form.get('rating', ''))
        except ValueError:
            rating = 0

        # Use only the field that matches the chosen type
        class_id = therapy_id = None
        raw_id = request.form.get('class_id' if booking_type == 'class' else 'therapy_id', '')
        item_id = int(raw_id) if raw_id.isdigit() else None

        error = None
        if rating not in range(1, 6):
            error = 'Please provide a rating between 1 and 5.'
        elif booking_type not in ('class', 'therapy') or item_id is None:
            error = 'Please choose the class or therapy you want to review.'
        else:
            # The member must have an APPROVED booking for it
            column = 'class_id' if booking_type == 'class' else 'therapy_id'
            cursor.execute(
                f"SELECT 1 FROM bookings WHERE user_id=%s AND status='approved' "
                f"AND {column}=%s LIMIT 1", (user_id, item_id)
            )
            if not cursor.fetchone():
                error = 'You can only review sessions you have attended or booked.'

        if error:
            flash(error, 'warning')
        else:
            if booking_type == 'class':
                class_id = item_id
            else:
                therapy_id = item_id
            cursor.execute(
                'INSERT INTO feedback (user_id, class_id, therapy_id, rating, comments) '
                'VALUES (%s,%s,%s,%s,%s)',
                (user_id, class_id, therapy_id, rating, comments)
            )
            db.commit()
            flash('Thank you for your feedback!', 'success')
            cursor.close()
            return redirect(url_for('member.dashboard'))

    # Classes and therapies the member has had approved bookings for
    cursor.execute('''
        SELECT DISTINCT c.class_id, c.class_name
        FROM   bookings b JOIN classes c ON b.class_id = c.class_id
        WHERE  b.user_id=%s AND b.status='approved'
    ''', (user_id,))
    booked_classes = cursor.fetchall()

    cursor.execute('''
        SELECT DISTINCT t.therapy_id, t.therapy_name
        FROM   bookings b JOIN therapies t ON b.therapy_id = t.therapy_id
        WHERE  b.user_id=%s AND b.status='approved'
    ''', (user_id,))
    booked_therapies = cursor.fetchall()

    cursor.close()
    return render_template('member/feedback.html',
                           booked_classes=booked_classes,
                           booked_therapies=booked_therapies)


# ── BMI Calculator ────────────────────────────────────────────────────────────
@member_bp.route('/bmi', methods=['GET', 'POST'])
@member_required
def bmi_calculator():
    result   = None
    advice   = None
    suggestions = []

    if request.method == 'POST':
        try:
            weight = float(request.form.get('weight', 0))
            height = float(request.form.get('height', 0))

            if not (10 <= weight <= 300 and 50 <= height <= 250):
                flash('Please enter a realistic weight (10-300 kg) and height (50-250 cm).', 'warning')
                return render_template('member/bmi_calculator.html',
                                       result=None, suggestions=[])

            bmi, category = calculate_bmi(weight, height)
            advice        = get_bmi_advice(category)
            result        = {'bmi': bmi, 'category': category}

            # Fetch suggested classes from DB
            db     = get_db()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM classes WHERE (suggested_for=%s OR suggested_for='All') "
                "AND is_active=1 LIMIT 3",
                (category,)
            )
            suggestions = cursor.fetchall()
            cursor.close()

        except (ValueError, ZeroDivisionError):
            flash('Please enter valid numeric values.', 'danger')

    return render_template('member/bmi_calculator.html',
                           result=result, advice=advice,
                           suggestions=suggestions)


# ── Asana Library ─────────────────────────────────────────────────────────────
@member_bp.route('/asanas')
@member_required
def asana_library():
    difficulty_filter = request.args.get('difficulty', 'All')
    if difficulty_filter != 'All':
        filtered = [a for a in ASANA_LIBRARY if a['difficulty'] == difficulty_filter]
    else:
        filtered = ASANA_LIBRARY
    return render_template('member/asana_library.html',
                           asanas=filtered,
                           difficulty_filter=difficulty_filter,
                           difficulties=['All', 'Beginner', 'Intermediate', 'Advanced'])
