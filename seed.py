"""
Seed script for InternSpark.
Initializes the SQLite database with the schema and seeds:
1. Demo student account (with pre-filled skills and profile for instant recommendations).
2. Demo admin account.
3. Diverse sample internship listings across AI/ML, Data Science, Python, Web Development,
   Software Engineering, Cybersecurity, and Cloud Computing.

All listings are explicitly marked: [Demo Listing - For Local Development].
"""

import os
import sys
import sqlite3
import secrets
import string
from werkzeug.security import generate_password_hash

# Add current directory to path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, BASE_DIR)

from config import Config

def get_db_connection(db_path=None):
    if db_path is None:
        db_path = Config.DATABASE
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=None):
    """Executes schema.sql to ensure all tables exist."""
    schema_path = os.path.join(BASE_DIR, 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    conn = get_db_connection(db_path)
    with conn:
        conn.executescript(schema_sql)
    conn.close()
    print("Database schema successfully initialized.")

def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(chars) for _ in range(length))

def seed_data(db_path=None, student_pw=None, admin_pw=None, reset=False):
    init_db(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    if reset:
        print("Resetting existing demo data...")
        with conn:
            cursor.execute("DELETE FROM applications;")
            cursor.execute("DELETE FROM saved_internships;")
            cursor.execute("DELETE FROM internships;")
            cursor.execute("DELETE FROM student_profiles;")
            cursor.execute("DELETE FROM users;")

    # 1. Demo Student & Admin Accounts
    # Default known passwords for local development, or generated if not provided
    student_email = "student@internspark.demo"
    admin_email = "admin@internspark.demo"

    if not student_pw:
        student_pw = "Student@12345"
    if not admin_pw:
        admin_pw = "Admin@Secure2026"

    # Check if student exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (student_email,))
    student_row = cursor.fetchone()
    if not student_row:
        student_hash = generate_password_hash(student_pw)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'student')
        """, ("Alex Johnson", student_email, student_hash))
        student_id = cursor.lastrowid
        print(f"Created demo student account: {student_email} (Password: {student_pw})")
    else:
        student_id = student_row['id']

    # Seed student profile if not exists
    cursor.execute("SELECT id FROM student_profiles WHERE user_id = ?", (student_id,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO student_profiles (
                user_id, college, degree, semester, graduation_year,
                skills, interests, preferred_location, work_mode,
                duration_preference, bio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            student_id,
            "Apex Institute of Technology",
            "B.Tech in Computer Science",
            "6th Semester",
            2027,
            "Python, Flask, React, JavaScript, SQL, Git, Docker, Machine Learning",
            "AI/ML, Web Development, Cloud Computing",
            "San Francisco, CA / Remote",
            "Remote",
            "3 to 6 Months",
            "Passionate computer science student eager to build scalable web applications and explore applied AI systems. Active open-source contributor and hackathon participant."
        ))
        print("Created profile for demo student with sample skills & interests.")

    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (admin_email,))
    admin_row = cursor.fetchone()
    if not admin_row:
        admin_hash = generate_password_hash(admin_pw)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, 'admin')
        """, ("InternSpark Administrator", admin_email, admin_hash))
        print(f"Created demo admin account: {admin_email} (Password: {admin_pw})")

    # 2. Seed Sample Internship Listings
    sample_internships = [
        {
            "title": "Machine Learning Research Intern [Demo]",
            "company": "NeuralEdge Labs (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=120&auto=format&fit=crop&q=80",
            "description": "Collaborate with research scientists on state-of-the-art vision models and natural language processing pipelines. This demo listing highlights tasks in fine-tuning open foundation models, dataset curation, and latency optimization. (Demo Listing - For Local Development)",
            "required_skills": "Python, Machine Learning, PyTorch, SQL, Git",
            "category": "AI/ML",
            "location": "San Francisco, CA",
            "work_mode": "Hybrid",
            "duration": "6 Months",
            "stipend": "$3,200/month",
            "is_paid": 1,
            "application_deadline": "2026-11-30",
            "eligibility": "Undergraduate or Graduate students in CS, AI, or related fields with Python & ML foundations.",
            "application_url": "https://example.com/apply/ml-demo",
        },
        {
            "title": "Full-Stack Web Engineering Intern [Demo]",
            "company": "Veloce Cloud Solutions (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=120&auto=format&fit=crop&q=80",
            "description": "Build responsive, high-performance customer portals and internal tools. You will work across frontend interfaces and backend Flask/REST services. (Demo Listing - For Local Development)",
            "required_skills": "Python, Flask, JavaScript, React, SQL, HTML, CSS",
            "category": "Web Development",
            "location": "Remote",
            "work_mode": "Remote",
            "duration": "3 Months",
            "stipend": "$2,800/month",
            "is_paid": 1,
            "application_deadline": "2026-12-15",
            "eligibility": "Pre-final or final year engineering/CS students with hands-on web project experience.",
            "application_url": "https://example.com/apply/fullstack-demo",
        },
        {
            "title": "Data Science & Analytics Intern [Demo]",
            "company": "QuantumMetric Insights (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=120&auto=format&fit=crop&q=80",
            "description": "Turn raw business data into actionable dashboards and predictive statistical models. Work directly with analysts using pandas, SQL, and interactive visualizations. (Demo Listing - For Local Development)",
            "required_skills": "Python, SQL, Pandas, Data Analysis, Statistics",
            "category": "Data Science",
            "location": "New York, NY",
            "work_mode": "Hybrid",
            "duration": "4 Months",
            "stipend": "$2,500/month",
            "is_paid": 1,
            "application_deadline": "2026-11-20",
            "eligibility": "Students majoring in Statistics, Mathematics, Data Science, or Computer Science.",
            "application_url": "https://example.com/apply/datasci-demo",
        },
        {
            "title": "Backend Systems & Python Intern [Demo]",
            "company": "CoreGrid Distributed Tech (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=120&auto=format&fit=crop&q=80",
            "description": "Design asynchronous worker tasks, robust RESTful APIs, and database schemas with high concurrency. Practice automated testing and CI/CD best practices. (Demo Listing - For Local Development)",
            "required_skills": "Python, Flask, SQL, Docker, Linux, Git",
            "category": "Python",
            "location": "Austin, TX",
            "work_mode": "Remote",
            "duration": "6 Months",
            "stipend": "$3,000/month",
            "is_paid": 1,
            "application_deadline": "2026-12-01",
            "eligibility": "Strong fundamentals in object-oriented programming, data structures, and database design.",
            "application_url": "https://example.com/apply/backend-demo",
        },
        {
            "title": "Cybersecurity Operations & Defense Intern [Demo]",
            "company": "Fortress Shield Infosec (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=120&auto=format&fit=crop&q=80",
            "description": "Perform vulnerability assessments, review network security logs, and assist with penetration testing scripts. Gain hands-on exposure to defensive tooling. (Demo Listing - For Local Development)",
            "required_skills": "Cybersecurity, Linux, Python, Networking, Wireshark",
            "category": "Cybersecurity",
            "location": "Boston, MA",
            "work_mode": "On-site",
            "duration": "3 Months",
            "stipend": "$2,600/month",
            "is_paid": 1,
            "application_deadline": "2026-10-31",
            "eligibility": "Enrolled in Cybersecurity or Information Systems program with basic networking certs or coursework.",
            "application_url": "https://example.com/apply/cyber-demo",
        },
        {
            "title": "Cloud Infrastructure & DevOps Intern [Demo]",
            "company": "SkyScale Cloud Platform (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=120&auto=format&fit=crop&q=80",
            "description": "Automate containerized deployments, monitor telemetry pipelines, and help configure Terraform cloud infrastructure templates. (Demo Listing - For Local Development)",
            "required_skills": "Cloud Computing, Docker, Kubernetes, Linux, Python, AWS",
            "category": "Cloud Computing",
            "location": "Seattle, WA",
            "work_mode": "Remote",
            "duration": "6 Months",
            "stipend": "$3,400/month",
            "is_paid": 1,
            "application_deadline": "2026-11-25",
            "eligibility": "Students familiar with container orchestration, cloud fundamentals, and command-line automation.",
            "application_url": "https://example.com/apply/devops-demo",
        },
        {
            "title": "Junior Software Engineering Intern [Demo]",
            "company": "Apex Dynamics (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=120&auto=format&fit=crop&q=80",
            "description": "Work side-by-side with senior engineers on core product features, refactoring legacy components, and writing unit tests. Great mentorship culture. (Demo Listing - For Local Development)",
            "required_skills": "Java, Python, C++, Data Structures, Algorithms, Git",
            "category": "Software Engineering",
            "location": "Chicago, IL",
            "work_mode": "Hybrid",
            "duration": "3 Months",
            "stipend": "$2,400/month",
            "is_paid": 1,
            "application_deadline": "2026-12-31",
            "eligibility": "All enrolled computer engineering / science students with solid algorithm fundamentals.",
            "application_url": "https://example.com/apply/swe-demo",
        },
        {
            "title": "AI Ethics & Model Evaluation Fellow [Demo]",
            "company": "OpenResponsible AI (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=120&auto=format&fit=crop&q=80",
            "description": "Evaluate generative model outputs for bias, toxicity, and hallucination metrics. Build automated testing benchmarks. (Demo Listing - For Local Development)",
            "required_skills": "Python, Machine Learning, NLP, Data Analysis",
            "category": "AI/ML",
            "location": "Remote",
            "work_mode": "Remote",
            "duration": "3 Months",
            "stipend": "$2,200/month",
            "is_paid": 1,
            "application_deadline": "2026-11-15",
            "eligibility": "Interdisciplinary interest in AI safety, linguistics, and machine learning benchmarking.",
            "application_url": "https://example.com/apply/ai-eval-demo",
        },
        {
            "title": "Non-Profit Tech & Open Education Intern [Demo]",
            "company": "CodeForGood Alliance (Demo)",
            "logo_url": "https://images.unsplash.com/photo-1531482615713-2afd69097998?w=120&auto=format&fit=crop&q=80",
            "description": "Help develop free community STEM educational software. Flexible part-time hours for students looking for volunteer and portfolio-building experience. (Demo Listing - For Local Development)",
            "required_skills": "HTML, CSS, JavaScript, Git",
            "category": "Web Development",
            "location": "San Diego, CA",
            "work_mode": "Remote",
            "duration": "2 Months",
            "stipend": "Unpaid (Academic Credit)",
            "is_paid": 0,
            "application_deadline": "2026-11-10",
            "eligibility": "Open to all beginners and students seeking verified academic internship credit.",
            "application_url": "https://example.com/apply/community-demo",
        }
    ]

    for item in sample_internships:
        cursor.execute("SELECT id FROM internships WHERE title = ? AND company = ?", (item['title'], item['company']))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO internships (
                    title, company, logo_url, description, required_skills,
                    category, location, work_mode, duration, stipend,
                    is_paid, application_deadline, eligibility, application_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item['title'], item['company'], item['logo_url'], item['description'],
                item['required_skills'], item['category'], item['location'],
                item['work_mode'], item['duration'], item['stipend'], item['is_paid'],
                item['application_deadline'], item['eligibility'], item['application_url']
            ))

    # Also seed a sample saved internship and application for the demo student
    cursor.execute("SELECT id FROM internships LIMIT 2")
    sample_intern_rows = cursor.fetchall()
    if len(sample_intern_rows) >= 2:
        # Save first internship
        first_id = sample_intern_rows[0]['id']
        second_id = sample_intern_rows[1]['id']

        cursor.execute("SELECT id FROM saved_internships WHERE user_id = ? AND internship_id = ?", (student_id, first_id))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO saved_internships (user_id, internship_id) VALUES (?, ?)", (student_id, first_id))

        cursor.execute("SELECT id FROM applications WHERE user_id = ? AND internship_id = ?", (student_id, second_id))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO applications (user_id, internship_id, status, notes)
                VALUES (?, ?, 'Applied', 'Submitted resume and portfolio link through demo portal.')
            """, (student_id, second_id))

    conn.commit()
    conn.close()
    print("Seed process completed successfully!")
    print("=" * 60)
    print("DEMO CREDENTIALS (LOCAL DEVELOPMENT ONLY):")
    print(f"Student: Email: {student_email} | Password: {student_pw}")
    print(f"Admin:   Email: {admin_email}   | Password: {admin_pw}")
    print("=" * 60)

if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_data(reset=reset_flag)
