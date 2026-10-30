"""
blueprints/auth/routes.py — Login, Register, Logout
"""

from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash, generate_password_hash

from blueprints.auth import auth_bp
from utils.db import get_db
from utils.helpers import clean_gender, clean_phone


# ── Helper: redirect user to their role's dashboard ──────────────────────────
def redirect_by_role(role):
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    if role == 'instructor':
        return redirect(url_for('instructor.dashboard'))
    return redirect(url_for('member.dashboard'))


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Already logged in → send to dashboard
    if 'user_id' in session:
        return redirect_by_role(session['role'])

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        # Basic validation
        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('auth/login.html')

        db     = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            'SELECT * FROM users WHERE email = %s AND is_active = 1',
            (email,)
        )
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id']   = user['user_id']
            session['user_name'] = user['full_name']
            session['role']      = user['role']
            session['email']     = user['email']
            flash(f"Welcome back, {user['full_name']}! 🙏", 'success')
            return redirect_by_role(user['role'])
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')


# ── Register ──────────────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect_by_role(session['role'])

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email     = request.form.get('email', '').strip().lower()
        phone     = request.form.get('phone', '').strip()
        gender    = request.form.get('gender', '')
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        # Server-side validation
        errors = []
        if not full_name or len(full_name) > 100:
            errors.append('Full name is required (max 100 characters).')
        if not email or '@' not in email or len(email) > 150:
            errors.append('A valid email address is required.')
        phone_value = clean_phone(phone, errors)
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm:
            errors.append('Passwords do not match.')

        if errors:
            for err in errors:
                flash(err, 'danger')
            return render_template('auth/register.html',
                                   form=request.form)

        db     = get_db()
        cursor = db.cursor(dictionary=True)

        # Check duplicate email
        cursor.execute('SELECT user_id FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            flash('That email is already registered. Please log in.', 'warning')
            cursor.close()
            return render_template('auth/register.html', form=request.form)

        # Insert new member
        hashed = generate_password_hash(password)
        cursor.execute(
            'INSERT INTO users (full_name, email, password_hash, role, phone, gender) '
            'VALUES (%s, %s, %s, %s, %s, %s)',
            (full_name, email, hashed, 'member', phone_value, clean_gender(gender))
        )
        db.commit()
        cursor.close()

        flash('Registration successful! You can now log in. 🎉', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form={})


# ── Logout ────────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {name}! See you on the mat. 🧘', 'info')
    return redirect(url_for('auth.login'))
