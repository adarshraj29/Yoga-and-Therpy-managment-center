# Yoga and Therapy Center Management System

MCA mini project built with **Python Flask** and **MySQL** (plain SQL, no ORM).

Three roles: **Admin**, **Member**, **Instructor**. Features: session login with hashed passwords,
class and therapy booking with seat control, admin approval, attendance, feedback, a BMI calculator
that suggests classes, and an Asana library.

---

## 1. Requirements

| Software | Version | Notes |
|---|---|---|
| Python | 3.10 or newer | Tick **"Add Python to PATH"** during installation |
| MySQL Server | 8.0 or newer | Install **MySQL Workbench** too (easiest way to import the schema) |

---

## 2. Step-by-step run guide (Windows)

1. **Open the project folder** (the one containing `app.py`) in VS Code or Command Prompt.
2. **Create a virtual environment**
   ```
   python -m venv venv
   ```
3. **Activate it**
   ```
   venv\Scripts\activate
   ```
   (Mac/Linux: `source venv/bin/activate`). The prompt should now start with `(venv)`.
4. **Install the packages**
   ```
   pip install -r requirements.txt
   ```
5. **Set your MySQL password** in `config.py`: put it between the quotes of `MYSQL_PASSWORD`.
   (`seed.py` reads the same file, so you only set it once.)
6. **Create the database.** Use ONE of these:
   - **MySQL Workbench:** open a connection, then *File > Open SQL Script*, choose `schema.sql`,
     and click the lightning-bolt (Execute) button.
   - **Command line:** `mysql -u root -p < schema.sql`
     (do **not** add the database name; the script creates it).
   - `schema.sql` starts with `DROP DATABASE`, so importing it again wipes the data. That is the reset button.
7. **Load the sample data (run once)**
   ```
   python seed.py
   ```
8. **Start the app**
   ```
   python app.py
   ```
9. **Open** <http://127.0.0.1:5000> in your browser.

### Demo logins

| Role | Email | Password |
|---|---|---|
| Admin | admin@yogacenter.com | admin123 |
| Instructor | priya@yogacenter.com | instructor123 |
| Instructor | rahul@yogacenter.com | instructor123 |
| Member | member@yogacenter.com | member123 |

Any new person who registers on the site becomes a **member**.

---

## 2b. Using XAMPP instead of MySQL Workbench

1. Open the XAMPP Control Panel and **Start MySQL** (Apache is not needed).
2. Import the database from Command Prompt (adjust the path to where XAMPP is installed):
   ```
   cd /d "D:\yoga and therpy center\yoga_therapy"
   D:\XAMPP\mysql\bin\mysql.exe -u root < schema.sql
   ```
3. Leave `MYSQL_PASSWORD` empty in `config.py` (XAMPP's default root password is blank).
4. Continue from step 7 of the guide above (`python seed.py`, then `python app.py`).

## 2c. Replacing an older copy with this version

1. Stop the running app (Ctrl+C in its Command Prompt window).
2. Copy everything from this folder over your old project folder and choose **Replace**. Keep your `venv` folder.
3. Re-import `schema.sql` (it resets `yoga_therapy_db` only) and run `python seed.py` once.
4. Start the app with `python app.py` and press **Ctrl+F5** in the browser so the new styles load.

> The login page has one-click **demo account** buttons for presentations. Delete the
> `demo-box` block in `templates/auth/login.html` before using the system for real.

---

## 3. Common errors and fixes

| Error | Cause and fix |
|---|---|
| `ModuleNotFoundError: No module named 'mysql'` or `flask` | Virtual environment not activated, or step 4 skipped. Activate it and run `pip install -r requirements.txt`. |
| `Access denied for user 'root'@'localhost'` | Password in `config.py` does not match your MySQL password. |
| `Unknown database 'yoga_therapy_db'` | `schema.sql` was not imported (step 6). |
| `Can't connect to MySQL server on 'localhost'` | MySQL service is not running. Start it from Windows *Services* (MySQL80). |
| `'mysql' is not recognized` | MySQL `bin` folder is not on PATH. Use MySQL Workbench for step 6 instead. |
| `Address already in use` / port 5000 busy | Change `port=5000` to `5001` at the bottom of `app.py`. |
| `[SKIP] The database already contains data` | `seed.py` was already run. Re-import `schema.sql` to start fresh. |

---

## 4. Project structure

```
yoga_therapy/
├── app.py            Flask app factory and entry point
├── config.py         Database settings, secret key
├── schema.sql        Tables, stored procedures, function, triggers, view
├── seed.py           Sample users, classes, therapies, instructors
├── blueprints/       auth, admin, member, instructor (each has routes.py)
├── utils/            db.py (connection), decorators.py (role access), bmi.py, helpers.py (validation)
├── templates/        Jinja2 pages (base, auth, admin, member, instructor, errors)
└── static/           css/style.css, js/main.js
```

---

## 5. Database objects (for your viva)

| Object | Name | What it does |
|---|---|---|
| Stored procedure | `sp_book_session` | Checks for a duplicate booking and for free seats, then inserts the booking. Returns a result code through an OUT parameter. Flask calls it with `cursor.callproc()`. |
| Stored procedure | `sp_cancel_booking` | Cancels a booking only if it belongs to the user and is pending or approved. |
| Stored function | `fn_available_seats(class_id, date)` | Total seats minus pending and approved bookings **for that date**. |
| Trigger | `trg_booking_log` | Writes every booking status change into `booking_log` (audit trail). |
| Trigger | `trg_before_attendance_insert` | Rejects attendance for any booking that is not approved. |
| View | `vw_booking_details` | Joins bookings, users, classes and therapies for the admin pages. |

**How seats work:** a class repeats every week, so seats are counted **per session date**, not as one
global counter. Cancelling or rejecting a booking frees its seat automatically because
`fn_available_seats` only counts pending and approved bookings. MySQL does not support Oracle PL/SQL;
these are MySQL stored routines, which do the same job.

---

## 6. Features by role

**Admin:** dashboard statistics; add, edit and deactivate classes, therapies and instructors;
approve or reject bookings; view members and feedback.

**Member:** register and log in; browse classes (with seats left for the next session) and therapies;
book a session; view and cancel bookings; submit a rating and comments; BMI calculator with class
suggestions; Asana library with difficulty filter.

**Instructor:** dashboard; list of assigned sessions; mark attendance (only for own approved
sessions, on or after the session date).

**Booking rules:** a class can only be booked on its weekday and always uses its fixed time;
therapies let the member choose a time slot; past dates are rejected; the same session cannot be
booked twice; a full session cannot be booked.

---

## 7. Test cases

| ID | Scenario | Steps | Expected result |
|---|---|---|---|
| TC01 | Member registration | Register with name, email, password (6+ chars), gender left blank | Account created, redirected to login |
| TC02 | Duplicate email | Register again with the same email | "Email already registered" message |
| TC03 | Bad phone number | Register with phone `abc` | Validation error, no crash |
| TC04 | Valid login | Log in as member@yogacenter.com | Redirected to member dashboard |
| TC05 | Wrong password | Log in with a wrong password | "Invalid email or password" |
| TC06 | Role protection | As a member, open `/admin/dashboard` | Redirected to login with "Admin access only" |
| TC07 | Book a class | Member > Classes > Book Now, pick a date on the class weekday | Booking created with status **pending** |
| TC08 | Wrong weekday | Pick a date that is not the class weekday | Rejected with a message naming the weekday |
| TC09 | Past date | Pick a date before today | "Please choose a future date" |
| TC10 | Duplicate booking | Book the same class on the same date twice | "Already booked this session" |
| TC11 | Full session | Fill all seats for one date, then book again | "No seats available for that date" |
| TC12 | Book a therapy | Choose a therapy, date and time slot | Booking created as pending |
| TC13 | Approve booking | Admin > Bookings > Approve | Status becomes **approved**; entry appears in `booking_log` |
| TC14 | Reject booking | Admin rejects a pending booking | Status becomes **rejected**; seat is freed |
| TC15 | Approve a cancelled booking | Member cancels, admin tries to approve | Refused: "cannot be approved" |
| TC16 | Cancel booking | Member > My Bookings > Cancel | Status **cancelled**; seat available again |
| TC17 | Add class (valid) | Admin adds a class with valid data | Class appears in the list |
| TC18 | Add class (invalid) | Seats `-3`, duration `abc`, empty name | Error messages shown, nothing saved |
| TC19 | Edit morning class | Admin edits a 7:00 AM class | Time field shows 07:00 and saves correctly |
| TC20 | Deactivate instructor | Admin deactivates an instructor | Instructor cannot log in; their classes become unassigned |
| TC21 | Mark attendance | Instructor marks an approved session on or after its date | "Attendance recorded" |
| TC22 | Attendance for another instructor | Change the booking id in the request | Refused: own approved sessions only |
| TC23 | Attendance before session date | Mark a future session | Refused with a warning |
| TC24 | Feedback | Member with an approved booking submits 4 stars | Saved; visible in Admin > Feedback |
| TC25 | BMI calculator | Weight 80 kg, height 170 cm | BMI 27.7 Overweight, suggests Power Vinyasa |
| TC26 | BMI out of range | Height 0 or 500 | Realistic-range warning, no result |
| TC27 | Asana filter | Asana Library > Beginner | Only beginner poses shown |
| TC28 | Logout | Click logout | Session cleared, login page shown |

---

## 8. Known limitations (be ready to mention these)

- No CSRF tokens on forms (acceptable for a local academic demo; Flask-WTF would add them).
- Uses Flask's built-in development server; a production deployment needs Gunicorn or Waitress and a new `SECRET_KEY`.
- No payment gateway, email or SMS (out of scope for a mini project).
- Deactivated instructors cannot be re-activated from the UI.

---

## 9. Future scope

Online payments, email/SMS reminders, class calendar view, membership plans, progress charts, PDF invoices.
