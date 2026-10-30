"""
seed.py — Sample Data Seeder
Run this AFTER importing schema.sql into MySQL.

Steps:
  1. mysql -u root -p < schema.sql          (schema.sql creates the database itself)
  2. Edit config.py with your MySQL password
  3. python seed.py                         (run it ONCE; re-import schema.sql to reset)

Default credentials after seeding:
  Admin      : admin@yogacenter.com    / admin123
  Instructor1: priya@yogacenter.com    / instructor123
  Instructor2: rahul@yogacenter.com    / instructor123
  Member     : member@yogacenter.com   / member123
"""

import mysql.connector
from mysql.connector import errors as mysql_errors
from werkzeug.security import generate_password_hash

# Connection settings are read from config.py, so the password is set in ONE place.
from config import Config

DB_CONFIG = {
    'host':     Config.MYSQL_HOST,
    'user':     Config.MYSQL_USER,
    'password': Config.MYSQL_PASSWORD,
    'database': Config.MYSQL_DATABASE,
    'port':     Config.MYSQL_PORT,
}


def seed():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
    except mysql_errors.Error as exc:
        print(f"[ERROR] Could not connect to MySQL: {exc}")
        print("        Check MYSQL_PASSWORD in config.py and that schema.sql was imported.")
        raise SystemExit(1)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        print("[SKIP] The database already contains data. To start fresh, re-import schema.sql, then run seed.py again.")
        cursor.close(); conn.close()
        return

    print("Seeding yoga_therapy_db ...")

    # ----------------------------------------------------------
    # 1. USERS  (1 admin + 2 instructors + 1 demo member)
    # ----------------------------------------------------------
    users = [
        ('Admin User',    'admin@yogacenter.com',    generate_password_hash('admin123'),       'admin',      '9000000001', 'Male'),
        ('Priya Sharma',  'priya@yogacenter.com',    generate_password_hash('instructor123'),  'instructor', '9000000002', 'Female'),
        ('Rahul Verma',   'rahul@yogacenter.com',    generate_password_hash('instructor123'),  'instructor', '9000000003', 'Male'),
        ('Ananya Singh',  'member@yogacenter.com',   generate_password_hash('member123'),      'member',     '9000000004', 'Female'),
    ]
    cursor.executemany(
        'INSERT INTO users (full_name, email, password_hash, role, phone, gender) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        users
    )

    # ----------------------------------------------------------
    # 2. INSTRUCTOR PROFILES  (linked to user_id 2 and 3)
    # ----------------------------------------------------------
    instructors = [
        (2, 'Hatha Yoga, Pranayama', 8,
         'Priya is a certified Hatha Yoga instructor with 8 years of therapeutic experience.',
         'RYT-500, Yoga Alliance'),
        (3, 'Power Yoga, Meditation', 5,
         'Rahul specialises in dynamic Power Yoga and mindfulness-based stress reduction.',
         'RYT-200, International Yoga Federation'),
    ]
    cursor.executemany(
        'INSERT INTO instructors (user_id, specialization, experience_years, bio, certification) '
        'VALUES (%s, %s, %s, %s, %s)',
        instructors
    )

    # ----------------------------------------------------------
    # 3. YOGA CLASSES  (5 classes)
    # instructor_id 1 = Priya, instructor_id 2 = Rahul
    # ----------------------------------------------------------
    classes = [
        ('Morning Hatha Flow',
         'A gentle morning session focusing on foundational postures, breathing, and flexibility. Perfect for beginners.',
         1, 'Monday', '07:00:00', 60, 20, 20, 500.00, 'Beginner', 'Normal'),

        ('Power Vinyasa',
         'A dynamic, fast-paced sequence that builds strength, stamina, and mental focus.',
         2, 'Wednesday', '18:00:00', 75, 15, 15, 700.00, 'Advanced', 'Overweight'),

        ('Restorative Yoga',
         'Slow, supported postures held for longer durations. Ideal for stress relief and active recovery.',
         1, 'Friday', '10:00:00', 90, 12, 12, 600.00, 'Restorative', 'Obese'),

        ('Meditation and Pranayama',
         'Breathwork and guided meditation to calm the mind and improve lung capacity.',
         1, 'Tuesday', '08:00:00', 45, 25, 25, 400.00, 'All Levels', 'All'),

        ('Ashtanga Fundamentals',
         'Introduction to the eight-limbed Ashtanga system. Builds discipline and core strength.',
         2, 'Saturday', '09:00:00', 90, 18, 18, 800.00, 'Intermediate', 'Underweight'),
    ]
    cursor.executemany(
        'INSERT INTO classes '
        '(class_name, description, instructor_id, day_of_week, class_time, '
        ' duration_minutes, total_seats, available_seats, fee, level, suggested_for) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
        classes
    )

    # ----------------------------------------------------------
    # 4. THERAPY SERVICES  (4 therapies)
    # ----------------------------------------------------------
    therapies = [
        ('Abhyanga Oil Massage',
         'Traditional Ayurvedic full-body oil massage to detoxify, nourish skin, and calm the nervous system.',
         60, 1200.00),

        ('Shirodhara',
         'Warm herbal oil poured in a continuous stream over the forehead to induce deep mental relaxation.',
         45, 1500.00),

        ('Acupressure Therapy',
         'Targeted pressure on specific meridian points to relieve pain, improve circulation, and restore energy flow.',
         60, 1000.00),

        ('Sound Healing',
         'Tibetan singing bowls and tuning forks used to realign body frequencies and reduce anxiety.',
         30, 800.00),
    ]
    cursor.executemany(
        'INSERT INTO therapies (therapy_name, description, duration_minutes, fee) '
        'VALUES (%s, %s, %s, %s)',
        therapies
    )

    conn.commit()
    cursor.close()
    conn.close()
    print("[OK] Seeding complete!")
    print()
    print("  Admin      -> admin@yogacenter.com   / admin123")
    print("  Instructor -> priya@yogacenter.com   / instructor123")
    print("  Instructor -> rahul@yogacenter.com   / instructor123")
    print("  Member     -> member@yogacenter.com  / member123")


if __name__ == '__main__':
    seed()
