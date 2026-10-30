-- ============================================================
-- Yoga and Therapy Center Management System
-- Database : yoga_therapy_db
-- MySQL 8.x Schema — Pure DDL (no user inserts here)
-- Run seed.py after importing this file to populate data.
-- ============================================================

DROP DATABASE IF EXISTS yoga_therapy_db;
CREATE DATABASE yoga_therapy_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE yoga_therapy_db;

-- ============================================================
-- TABLE: users
-- Stores all users (admin / member / instructor)
-- ============================================================
CREATE TABLE users (
    user_id       INT            NOT NULL AUTO_INCREMENT,
    full_name     VARCHAR(100)   NOT NULL,
    email         VARCHAR(150)   NOT NULL UNIQUE,
    password_hash VARCHAR(255)   NOT NULL,
    role          ENUM('admin','member','instructor') NOT NULL DEFAULT 'member',
    phone         VARCHAR(15),
    gender        ENUM('Male','Female','Other'),
    date_of_birth DATE,
    address       TEXT,
    is_active     TINYINT(1)     NOT NULL DEFAULT 1,
    created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: instructors
-- Extended profile for users with role='instructor'
-- ============================================================
CREATE TABLE instructors (
    instructor_id    INT          NOT NULL AUTO_INCREMENT,
    user_id          INT          NOT NULL UNIQUE,
    specialization   VARCHAR(200),
    experience_years INT          DEFAULT 0,
    bio              TEXT,
    certification    VARCHAR(200),
    is_active        TINYINT(1)   NOT NULL DEFAULT 1,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (instructor_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: classes
-- Yoga classes offered at the center
-- suggested_for maps BMI category → suitable class
-- ============================================================
CREATE TABLE classes (
    class_id        INT           NOT NULL AUTO_INCREMENT,
    class_name      VARCHAR(150)  NOT NULL,
    description     TEXT,
    instructor_id   INT,
    day_of_week     ENUM('Monday','Tuesday','Wednesday','Thursday',
                         'Friday','Saturday','Sunday') NOT NULL,
    class_time      TIME          NOT NULL,
    duration_minutes INT          NOT NULL DEFAULT 60,
    total_seats     INT           NOT NULL DEFAULT 20,
    available_seats INT           NOT NULL DEFAULT 20,  -- legacy; real availability is per date via fn_available_seats()
    fee             DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    level           ENUM('Beginner','Intermediate','Advanced',
                         'Restorative','All Levels') NOT NULL DEFAULT 'All Levels',
    suggested_for   ENUM('Underweight','Normal','Overweight',
                         'Obese','All')               NOT NULL DEFAULT 'All',
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (class_id),
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: therapies
-- Therapy services offered at the center
-- ============================================================
CREATE TABLE therapies (
    therapy_id       INT           NOT NULL AUTO_INCREMENT,
    therapy_name     VARCHAR(150)  NOT NULL,
    description      TEXT,
    duration_minutes INT           NOT NULL DEFAULT 60,
    fee              DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    is_active        TINYINT(1)    NOT NULL DEFAULT 1,
    created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (therapy_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: bookings
-- Single table for both class and therapy bookings
-- booking_type distinguishes them
-- ============================================================
CREATE TABLE bookings (
    booking_id   INT    NOT NULL AUTO_INCREMENT,
    user_id      INT    NOT NULL,
    booking_type ENUM('class','therapy') NOT NULL,
    class_id     INT    DEFAULT NULL,
    therapy_id   INT    DEFAULT NULL,
    session_date DATE   NOT NULL,
    time_slot    TIME   NOT NULL,
    status       ENUM('pending','approved','rejected','cancelled')
                        NOT NULL DEFAULT 'pending',
    notes        TEXT,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (booking_id),
    FOREIGN KEY (user_id)     REFERENCES users(user_id)       ON DELETE CASCADE,
    FOREIGN KEY (class_id)    REFERENCES classes(class_id)    ON DELETE SET NULL,
    FOREIGN KEY (therapy_id)  REFERENCES therapies(therapy_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: booking_log
-- Audit trail populated automatically by trigger
-- ============================================================
CREATE TABLE booking_log (
    log_id      INT         NOT NULL AUTO_INCREMENT,
    booking_id  INT         NOT NULL,
    old_status  VARCHAR(20),
    new_status  VARCHAR(20),
    changed_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id)
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: feedback
-- Member star-rating and comments
-- ============================================================
CREATE TABLE feedback (
    feedback_id  INT  NOT NULL AUTO_INCREMENT,
    user_id      INT  NOT NULL,
    class_id     INT  DEFAULT NULL,
    therapy_id   INT  DEFAULT NULL,
    rating       INT  NOT NULL,
    comments     TEXT,
    submitted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (feedback_id),
    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5),
    FOREIGN KEY (user_id)    REFERENCES users(user_id)        ON DELETE CASCADE,
    FOREIGN KEY (class_id)   REFERENCES classes(class_id)     ON DELETE SET NULL,
    FOREIGN KEY (therapy_id) REFERENCES therapies(therapy_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- ============================================================
-- TABLE: attendance
-- Instructor marks attendance per approved booking
-- ============================================================
CREATE TABLE attendance (
    attendance_id INT       NOT NULL AUTO_INCREMENT,
    booking_id    INT       NOT NULL,
    instructor_id INT       NOT NULL,
    session_date  DATE      NOT NULL,
    is_present    TINYINT(1) NOT NULL DEFAULT 0,
    remarks       VARCHAR(255),
    marked_at     DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (attendance_id),
    FOREIGN KEY (booking_id)    REFERENCES bookings(booking_id)       ON DELETE CASCADE,
    FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- STORED FUNCTION: fn_available_seats
-- Returns real-time available seats for a class on a given date
-- Usage: SELECT fn_available_seats(class_id, '2024-12-25');
-- ============================================================
DELIMITER $$

CREATE FUNCTION fn_available_seats(p_class_id INT, p_session_date DATE)
RETURNS INT
READS SQL DATA
BEGIN
    DECLARE v_total   INT DEFAULT 0;
    DECLARE v_booked  INT DEFAULT 0;

    SELECT total_seats INTO v_total
    FROM   classes
    WHERE  class_id = p_class_id;

    SELECT COUNT(*) INTO v_booked
    FROM   bookings
    WHERE  class_id     = p_class_id
      AND  session_date = p_session_date
      AND  status IN ('pending', 'approved');

    RETURN GREATEST(v_total - v_booked, 0);
END$$

DELIMITER ;


-- ============================================================
-- STORED PROCEDURE: sp_book_session
-- Checks availability then inserts a booking row.
-- OUT p_result_code: 0 = success | 1 = no seats | 2 = already booked
-- Flask call: cursor.callproc('sp_book_session', args)
-- ============================================================
DELIMITER $$

CREATE PROCEDURE sp_book_session(
    IN  p_user_id      INT,
    IN  p_booking_type VARCHAR(10),
    IN  p_class_id     INT,
    IN  p_therapy_id   INT,
    IN  p_session_date DATE,
    IN  p_time_slot    TIME,
    OUT p_result_code  INT
)
BEGIN
    DECLARE v_seats          INT DEFAULT 0;
    DECLARE v_already_booked INT DEFAULT 0;

    -- Duplicate check: same user, same session, active status
    SELECT COUNT(*) INTO v_already_booked
    FROM   bookings
    WHERE  user_id       = p_user_id
      AND  booking_type  = p_booking_type
      AND  session_date  = p_session_date
      AND  (
              (p_booking_type = 'class'   AND class_id   = p_class_id)
           OR (p_booking_type = 'therapy' AND therapy_id = p_therapy_id)
           )
      AND  status NOT IN ('cancelled','rejected');

    IF v_already_booked > 0 THEN
        SET p_result_code = 2;  -- duplicate

    ELSEIF p_booking_type = 'class' THEN
        SET v_seats = fn_available_seats(p_class_id, p_session_date);

        IF v_seats <= 0 THEN
            SET p_result_code = 1;  -- no seats
        ELSE
            INSERT INTO bookings
                (user_id, booking_type, class_id, therapy_id, session_date, time_slot, status)
            VALUES
                (p_user_id, 'class', p_class_id, NULL, p_session_date, p_time_slot, 'pending');
            SET p_result_code = 0;  -- success
        END IF;

    ELSE
        -- Therapy has no seat limit
        INSERT INTO bookings
            (user_id, booking_type, class_id, therapy_id, session_date, time_slot, status)
        VALUES
            (p_user_id, 'therapy', NULL, p_therapy_id, p_session_date, p_time_slot, 'pending');
        SET p_result_code = 0;  -- success
    END IF;
END$$

DELIMITER ;


-- ============================================================
-- STORED PROCEDURE: sp_cancel_booking
-- Cancels a booking owned by the user (pending or approved only).
-- Seats are counted per session date by fn_available_seats(), which
-- only counts pending/approved bookings, so cancelling frees the seat
-- automatically - no counter needs to be restored.
-- OUT p_result_code: 0 = success | 1 = not allowed
-- ============================================================
DELIMITER $$

CREATE PROCEDURE sp_cancel_booking(
    IN  p_booking_id  INT,
    IN  p_user_id     INT,
    OUT p_result_code INT
)
BEGIN
    DECLARE v_status VARCHAR(20);
    DECLARE v_owner  INT;

    SELECT status, user_id
    INTO   v_status, v_owner
    FROM   bookings
    WHERE  booking_id = p_booking_id;

    -- Must be the owner and in a cancellable state
    IF v_owner IS NULL OR v_owner <> p_user_id THEN
        SET p_result_code = 1;

    ELSEIF v_status NOT IN ('pending','approved') THEN
        SET p_result_code = 1;

    ELSE
        UPDATE bookings
        SET    status = 'cancelled'
        WHERE  booking_id = p_booking_id;

        SET p_result_code = 0;
    END IF;
END$$

DELIMITER ;


-- ============================================================
-- TRIGGER: trg_before_attendance_insert
-- Data-integrity guard: attendance can only be recorded for an
-- APPROVED booking. Anything else is rejected with an error.
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_before_attendance_insert
BEFORE INSERT ON attendance
FOR EACH ROW
BEGIN
    DECLARE v_status VARCHAR(20);

    SELECT status INTO v_status
    FROM   bookings
    WHERE  booking_id = NEW.booking_id;

    IF v_status IS NULL OR v_status <> 'approved' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Attendance can only be marked for approved bookings';
    END IF;
END$$

DELIMITER ;


-- ============================================================
-- TRIGGER: trg_booking_log
-- Logs every status change into booking_log (audit trail)
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_booking_log
AFTER UPDATE ON bookings
FOR EACH ROW
BEGIN
    IF NEW.status <> OLD.status THEN
        INSERT INTO booking_log (booking_id, old_status, new_status, changed_at)
        VALUES (NEW.booking_id, OLD.status, NEW.status, NOW());
    END IF;
END$$

DELIMITER ;


-- ============================================================
-- VIEW: vw_booking_details
-- Flat, readable view used by admin to browse all bookings
-- ============================================================
CREATE VIEW vw_booking_details AS
SELECT
    b.booking_id,
    b.booking_type,
    b.session_date,
    b.time_slot,
    b.status,
    b.created_at        AS booked_on,
    u.user_id,
    u.full_name         AS member_name,
    u.email             AS member_email,
    u.phone             AS member_phone,
    c.class_name,
    c.level             AS class_level,
    c.fee               AS class_fee,
    t.therapy_name,
    t.fee               AS therapy_fee
FROM       bookings  b
JOIN       users     u  ON b.user_id    = u.user_id
LEFT JOIN  classes   c  ON b.class_id   = c.class_id
LEFT JOIN  therapies t  ON b.therapy_id = t.therapy_id;


-- ============================================================
-- NOTE: All sample data (users with hashed passwords, classes,
--       therapies, instructors) is inserted by seed.py.
--       Run:  python seed.py
--       after importing this schema.
-- ============================================================
