-- InternSpark Database Schema

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student' CHECK(role IN ('student', 'admin')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    college TEXT,
    degree TEXT,
    semester TEXT,
    graduation_year INTEGER,
    skills TEXT,
    interests TEXT,
    preferred_location TEXT,
    work_mode TEXT DEFAULT 'Remote' CHECK(work_mode IN ('Remote', 'Hybrid', 'On-site')),
    duration_preference TEXT,
    bio TEXT,
    resume_filename TEXT,
    resume_original_name TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    logo_url TEXT,
    description TEXT NOT NULL,
    required_skills TEXT NOT NULL,
    category TEXT NOT NULL,
    location TEXT NOT NULL,
    work_mode TEXT NOT NULL CHECK(work_mode IN ('Remote', 'Hybrid', 'On-site')),
    duration TEXT NOT NULL,
    stipend TEXT NOT NULL,
    is_paid INTEGER NOT NULL DEFAULT 1,
    application_deadline DATE,
    eligibility TEXT,
    application_url TEXT,
    posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS saved_internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    internship_id INTEGER NOT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, internship_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (internship_id) REFERENCES internships (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    internship_id INTEGER NOT NULL,
    applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'Interested' CHECK(status IN ('Interested', 'Applied', 'Interview', 'Offered', 'Rejected', 'Withdrawn')),
    notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, internship_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (internship_id) REFERENCES internships (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_internships_category ON internships(category);
CREATE INDEX IF NOT EXISTS idx_internships_work_mode ON internships(work_mode);
CREATE INDEX IF NOT EXISTS idx_saved_internships_user ON saved_internships(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id);
