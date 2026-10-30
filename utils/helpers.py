"""
utils/helpers.py - Small shared helpers: input validation and date/time utilities.
Keeps the route files short and readable.
"""

import re
from datetime import date, datetime, time, timedelta

DAYS       = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
              'Friday', 'Saturday', 'Sunday']
LEVELS     = ['Beginner', 'Intermediate', 'Advanced', 'Restorative', 'All Levels']
SUGGESTED  = ['Underweight', 'Normal', 'Overweight', 'Obese', 'All']
GENDERS    = ('Male', 'Female', 'Other')


# ── Input cleaning (each returns a value; errors are appended to a list) ─────

def clean_gender(value):
    """ENUM column: an empty or unknown value must become NULL, never ''."""
    return value if value in GENDERS else None


def clean_phone(value, errors):
    """Optional phone, 7-15 digits (column is VARCHAR(15)). Returns str or None."""
    value = (value or '').strip()
    if not value:
        return None
    digits = re.sub(r'[\s\-+()]', '', value)
    if not digits.isdigit() or not 7 <= len(digits) <= 15:
        errors.append('Phone number must contain 7 to 15 digits.')
        return None
    return digits


def parse_int(raw, label, errors, lo=0, hi=100000):
    try:
        number = int(str(raw).strip())
    except (ValueError, TypeError):
        errors.append(f'{label} must be a whole number.')
        return None
    if not lo <= number <= hi:
        errors.append(f'{label} must be between {lo} and {hi}.')
        return None
    return number


def parse_decimal(raw, label, errors, lo=0, hi=1000000):
    try:
        number = round(float(str(raw).strip()), 2)
    except (ValueError, TypeError):
        errors.append(f'{label} must be a number.')
        return None
    if not lo <= number <= hi:
        errors.append(f'{label} must be between {lo} and {hi}.')
        return None
    return number


def parse_time(raw, label, errors):
    """Accepts 'HH:MM' or 'HH:MM:SS'; returns 'HH:MM:00' for MySQL TIME."""
    match = re.fullmatch(r'(\d{1,2}):(\d{2})(?::\d{2})?', (raw or '').strip())
    if not match or int(match.group(1)) > 23 or int(match.group(2)) > 59:
        errors.append(f'{label} is not a valid time.')
        return None
    return f'{int(match.group(1)):02d}:{match.group(2)}:00'


def parse_choice(raw, allowed, label, errors):
    if raw not in allowed:
        errors.append(f'Please choose a valid {label}.')
        return None
    return raw


# ── Date helpers ──────────────────────────────────────────────────────────────

def next_session_date(day_name, today=None):
    """Next calendar date (today included) that falls on the class's weekday."""
    today = today or date.today()
    delta = (DAYS.index(day_name) - today.weekday()) % 7
    return today + timedelta(days=delta)


def weekday_name(d):
    return DAYS[d.weekday()]


# ── Jinja filters for MySQL TIME values (mysql-connector returns timedelta) ───

def _hour_minute(value):
    if isinstance(value, timedelta):
        secs = int(value.total_seconds())
        return (secs // 3600) % 24, (secs % 3600) // 60
    if isinstance(value, (time, datetime)):
        return value.hour, value.minute
    match = re.match(r'(\d{1,2}):(\d{2})', str(value))
    if match:
        return int(match.group(1)), int(match.group(2))
    return None


def clock(value):
    """7:00:00 -> '7:00 AM'"""
    if value in (None, ''):
        return ''
    hm = _hour_minute(value)
    if hm is None:
        return str(value)
    hour, minute = hm
    return f"{hour % 12 or 12}:{minute:02d} {'AM' if hour < 12 else 'PM'}"


def hhmm(value):
    """7:00:00 -> '07:00' (value format required by <input type=time>)"""
    hm = _hour_minute(value) if value not in (None, '') else None
    return f'{hm[0]:02d}:{hm[1]:02d}' if hm else ''
