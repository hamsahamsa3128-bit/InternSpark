"""
InternSpark - Modern Local Flask Internship Discovery & Recommendation Platform
"""

import os
import sqlite3
import secrets
import re
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, g, abort, send_from_directory, jsonify
)
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

from config import config_by_name
from recommendation_engine import RuleBasedRecommendationEngine

env_name = os.environ.get('FLASK_ENV', 'development')
app = Flask(__name__)
app.config.from_object(config_by_name.get(env_name, config_by_name['default']))

# Ensure required runtime folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'images'), exist_ok=True)


# ==========================================
# Database Helpers
# ==========================================

def get_db():
    """Returns an active SQLite connection stored on flask.g."""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Closes SQLite connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """Convenience helper to query the database."""
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=(), commit=True):
    """Convenience helper to execute an insert/update/delete."""
    db = get_db()
    cur = db.execute(query, args)
    last_id = cur.lastrowid
    if commit:
        db.commit()
    cur.close()
    return last_id


# ==========================================
# CSRF Protection & Context Processors
# ==========================================

def generate_csrf_token():
    """Generates or retrieves CSRF token in session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.before_request
def check_csrf():
    """Validates CSRF token on state-changing requests."""
    # Skip CSRF check in testing if configured
    if app.config.get('TESTING') and not app.config.get('WTF_CSRF_ENABLED', True):
        return

    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        # Allow checking either form field or header
        token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
        expected = session.get('_csrf_token')
        if not expected or not token or not secrets.compare_digest(token, expected):
            abort(400, description="Invalid or missing CSRF token. Please refresh the page and try again.")

@app.context_processor
def inject_global_data():
    """Injects user information and utility functions into all templates."""
    user = None
    saved_count = 0
    apps_count = 0
    if session.get('user_id'):
        user = query_db("SELECT id, name, email, role FROM users WHERE id = ?", (session['user_id'],), one=True)
        if user and user['role'] == 'student':
            s_row = query_db("SELECT COUNT(*) as count FROM saved_internships WHERE user_id = ?", (user['id'],), one=True)
            a_row = query_db("SELECT COUNT(*) as count FROM applications WHERE user_id = ?", (user['id'],), one=True)
            saved_count = s_row['count'] if s_row else 0
            apps_count = a_row['count'] if a_row else 0

    return {
        'current_user': user,
        'saved_count': saved_count,
        'apps_count': apps_count,
        'now_year': datetime.now().year
    }


# ==========================================
# Authentication & Authorization Decorators
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Admin login required.", "warning")
            return redirect(url_for('login', next=request.url))
        if session.get('role') != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ==========================================
# Business Logic Helpers
# ==========================================

def calculate_profile_completion(profile, user):
    """Calculates profile completion percentage based on filled fields."""
    if not profile or not user:
        return 0
    fields_to_check = [
        user['name'],
        user['email'],
        profile['college'],
        profile['degree'],
        profile['semester'],
        profile['graduation_year'],
        profile['skills'],
        profile['interests'],
        profile['preferred_location'],
        profile['work_mode'],
        profile['bio'],
        profile['resume_filename']
    ]
    filled = sum(1 for f in fields_to_check if f and str(f).strip())
    percentage = round((filled / len(fields_to_check)) * 100)
    return min(percentage, 100)

def allowed_file(filename):
    """Checks file extension against allowed whitelist."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# ==========================================
# Public & Home Routes
# ==========================================

@app.route('/')
def index():
    """Home landing page with hero, search, featured cards, statistics, and benefits."""
    # Fetch real counts from DB
    intern_count = query_db("SELECT COUNT(*) as c FROM internships WHERE is_active = 1", one=True)['c']
    company_count = query_db("SELECT COUNT(DISTINCT company) as c FROM internships WHERE is_active = 1", one=True)['c']
    student_count = query_db("SELECT COUNT(*) as c FROM users WHERE role = 'student'", one=True)['c']
    applications_count = query_db("SELECT COUNT(*) as c FROM applications", one=True)['c']

    # Fetch 6 featured internships
    featured_internships = query_db("""
        SELECT * FROM internships 
        WHERE is_active = 1 
        ORDER BY posted_date DESC 
        LIMIT 6
    """)

    # If student is logged in, attach recommendation scores
    internships_list = [dict(i) for i in featured_internships]
    if session.get('user_id') and session.get('role') == 'student':
        profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (session['user_id'],), one=True)
        if profile:
            internships_list = RuleBasedRecommendationEngine.rank_internships(dict(profile), internships_list)

    return render_template('index.html',
                           featured_internships=internships_list,
                           intern_count=intern_count,
                           company_count=company_count,
                           student_count=student_count,
                           applications_count=applications_count)


# ==========================================
# Authentication Routes
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration for new student accounts."""
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Server-side validations
        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template('register.html', name=name, email=email)

        # Basic email format check
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not re.match(email_regex, email):
            flash("Please enter a valid email address.", "danger")
            return render_template('register.html', name=name, email=email)

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template('register.html', name=name, email=email)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html', name=name, email=email)

        # Check duplicate email
        existing_user = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if existing_user:
            flash("An account with this email address already exists. Please log in.", "danger")
            return render_template('register.html', name=name, email=email)

        # Hash password securely
        password_hash = generate_password_hash(password)

        try:
            user_id = execute_db("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, 'student')
            """, (name, email, password_hash))

            # Initialize corresponding student profile
            execute_db("""
                INSERT INTO student_profiles (user_id)
                VALUES (?)
            """, (user_id,))

            # Establish session
            session.clear()
            session['user_id'] = user_id
            session['user_name'] = name
            session['user_email'] = email
            session['role'] = 'student'

            flash("Welcome to InternSpark! Your account was successfully created. Set up your profile now to get personalized recommendations.", "success")
            return redirect(url_for('profile'))
        except Exception as e:
            flash(f"Registration error: {str(e)}", "danger")
            return render_template('register.html', name=name, email=email)

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login with server-side validation and password verification."""
    if session.get('user_id'):
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        next_url = request.args.get('next')

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template('login.html', email=email)

        user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)
        if not user or not check_password_hash(user['password_hash'], password):
            flash("Invalid email or password. Please try again.", "danger")
            return render_template('login.html', email=email)

        # Reset session to prevent session fixation
        session.clear()
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_email'] = user['email']
        session['role'] = user['role']

        flash(f"Welcome back, {user['name']}!", "success")

        if user['role'] == 'admin':
            return redirect(next_url or url_for('admin_dashboard'))
        return redirect(next_url or url_for('dashboard'))

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    """Clears user session and logs out."""
    session.clear()
    flash("You have been securely logged out.", "info")
    return redirect(url_for('index'))


# ==========================================
# Student Dashboard & Profile Routes
# ==========================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard with profile completion, metrics, recommendations, and recent activity."""
    if session.get('role') == 'admin':
        return redirect(url_for('admin_dashboard'))

    user_id = session['user_id']
    user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), one=True)
    
    if not profile:
        execute_db("INSERT INTO student_profiles (user_id) VALUES (?)", (user_id,))
        profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), one=True)

    completion_pct = calculate_profile_completion(dict(profile), dict(user))

    # Real DB Counts
    saved_count = query_db("SELECT COUNT(*) as c FROM saved_internships WHERE user_id = ?", (user_id,), one=True)['c']
    app_count = query_db("SELECT COUNT(*) as c FROM applications WHERE user_id = ?", (user_id,), one=True)['c']

    # Fetch all active internships for recommendations
    all_internships = [dict(row) for row in query_db("SELECT * FROM internships WHERE is_active = 1")]
    recommended = RuleBasedRecommendationEngine.rank_internships(dict(profile), all_internships)

    # Count high matching internships (score >= 50%)
    matching_count = sum(1 for item in recommended if item['match_score'] >= 50)

    # Top 4 recommendations
    top_recommendations = recommended[:4]

    # Recently added internships (latest 4)
    recently_added = query_db("""
        SELECT * FROM internships 
        WHERE is_active = 1 
        ORDER BY posted_date DESC 
        LIMIT 4
    """)

    # Recent applications
    recent_apps = query_db("""
        SELECT a.id, a.status, a.applied_date, a.notes, i.title, i.company, i.location, i.id as internship_id
        FROM applications a
        JOIN internships i ON a.internship_id = i.id
        WHERE a.user_id = ?
        ORDER BY a.applied_date DESC
        LIMIT 4
    """, (user_id,))

    return render_template(
        'dashboard.html',
        user=user,
        profile=profile,
        completion_pct=completion_pct,
        saved_count=saved_count,
        app_count=app_count,
        matching_count=matching_count,
        recommendations=top_recommendations,
        recently_added=recently_added,
        recent_apps=recent_apps
    )


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Student profile view and update with safe resume upload."""
    user_id = session['user_id']
    user = query_db("SELECT * FROM users WHERE id = ?", (user_id,), one=True)
    profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), one=True)

    if not profile:
        execute_db("INSERT INTO student_profiles (user_id) VALUES (?)", (user_id,))
        profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), one=True)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        college = request.form.get('college', '').strip()
        degree = request.form.get('degree', '').strip()
        semester = request.form.get('semester', '').strip()
        grad_year_val = request.form.get('graduation_year', '').strip()
        graduation_year = int(grad_year_val) if grad_year_val and grad_year_val.isdigit() else None
        skills = request.form.get('skills', '').strip()
        interests = request.form.get('interests', '').strip()
        preferred_location = request.form.get('preferred_location', '').strip()
        work_mode = request.form.get('work_mode', 'Remote').strip()
        duration_preference = request.form.get('duration_preference', '').strip()
        bio = request.form.get('bio', '').strip()

        # Update name in users table if changed
        if name and name != user['name']:
            execute_db("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
            session['user_name'] = name

        resume_filename = profile['resume_filename']
        resume_original = profile['resume_original_name']

        # Handle resume file upload
        if 'resume' in request.files:
            file = request.files['resume']
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    flash("Invalid file format for resume. Only PDF (.pdf) and Word (.docx) files are accepted.", "danger")
                    return redirect(url_for('profile'))

                # Safe file saving with UUID prefix to prevent collisions and path traversal
                orig_clean = secure_filename(file.filename)
                ext = orig_clean.rsplit('.', 1)[1].lower() if '.' in orig_clean else 'pdf'
                safe_unique_name = f"{user_id}_{secrets.token_hex(8)}.{ext}"
                dest_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_unique_name)

                # Delete previous resume file if existed
                if resume_filename:
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_filename)
                    if os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass

                file.save(dest_path)
                resume_filename = safe_unique_name
                resume_original = orig_clean

        # Update student profile in SQLite
        execute_db("""
            UPDATE student_profiles SET
                college = ?, degree = ?, semester = ?, graduation_year = ?,
                skills = ?, interests = ?, preferred_location = ?, work_mode = ?,
                duration_preference = ?, bio = ?, resume_filename = ?, resume_original_name = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            college, degree, semester, graduation_year,
            skills, interests, preferred_location, work_mode,
            duration_preference, bio, resume_filename, resume_original,
            user_id
        ))

        flash("Your profile has been successfully updated!", "success")
        return redirect(url_for('profile'))

    completion_pct = calculate_profile_completion(dict(profile), dict(user))
    return render_template('profile.html', user=user, profile=profile, completion_pct=completion_pct)


@app.route('/profile/resume/download')
@login_required
def download_resume():
    """Authenticated download route for student's own resume (or admin)."""
    user_id = session['user_id']
    profile = query_db("SELECT resume_filename, resume_original_name FROM student_profiles WHERE user_id = ?", (user_id,), one=True)

    if not profile or not profile['resume_filename']:
        flash("No resume found on your profile.", "warning")
        return redirect(url_for('profile'))

    filename = profile['resume_filename']
    display_name = profile['resume_original_name'] or "Resume.pdf"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(file_path):
        flash("Resume file could not be located on the server.", "danger")
        return redirect(url_for('profile'))

    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True,
        download_name=display_name
    )


# ==========================================
# Internships & Search Routes
# ==========================================

@app.route('/internships')
def internships():
    """Database-backed search, combined filters, sorting, and pagination."""
    # Filter parameters
    q = request.args.get('q', '').strip()
    category = request.args.get('category', '').strip()
    work_mode = request.args.get('work_mode', '').strip()
    stipend_type = request.args.get('stipend_type', '').strip()  # 'paid', 'unpaid', or ''
    location = request.args.get('location', '').strip()
    sort_by = request.args.get('sort_by', 'newest').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 6

    # Base query construction with parameterized values
    where_clauses = ["is_active = 1"]
    params = []

    if q:
        where_clauses.append("(title LIKE ? OR company LIKE ? OR category LIKE ? OR required_skills LIKE ?)")
        search_term = f"%{q}%"
        params.extend([search_term, search_term, search_term, search_term])

    if category:
        where_clauses.append("category = ?")
        params.append(category)

    if work_mode:
        where_clauses.append("work_mode = ?")
        params.append(work_mode)

    if stipend_type == 'paid':
        where_clauses.append("is_paid = 1")
    elif stipend_type == 'unpaid':
        where_clauses.append("is_paid = 0")

    if location:
        where_clauses.append("location LIKE ?")
        params.append(f"%{location}%")

    where_sql = " AND ".join(where_clauses)

    # Fetch total count for pagination
    count_sql = f"SELECT COUNT(*) as count FROM internships WHERE {where_sql}"
    total_count = query_db(count_sql, params, one=True)['count']

    # Determine SQL sorting (Note: if user sorts by 'recommended', we sort in Python)
    if sort_by == 'deadline':
        order_sql = "ORDER BY application_deadline ASC NULLS LAST"
    elif sort_by == 'stipend':
        order_sql = "ORDER BY is_paid DESC, stipend DESC"
    else:  # 'newest' default
        order_sql = "ORDER BY posted_date DESC, id DESC"

    # Fetch all matching rows for sorting/ranking
    fetch_sql = f"SELECT * FROM internships WHERE {where_sql} {order_sql}"
    raw_results = [dict(r) for r in query_db(fetch_sql, params)]

    # Compute recommendations if student is logged in
    user_saved_ids = set()
    user_app_map = {}  # internship_id -> status

    if session.get('user_id') and session.get('role') == 'student':
        uid = session['user_id']
        profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (uid,), one=True)
        if profile:
            raw_results = RuleBasedRecommendationEngine.rank_internships(dict(profile), raw_results)
        
        saved_rows = query_db("SELECT internship_id FROM saved_internships WHERE user_id = ?", (uid,))
        user_saved_ids = {r['internship_id'] for r in saved_rows}

        app_rows = query_db("SELECT internship_id, status FROM applications WHERE user_id = ?", (uid,))
        user_app_map = {r['internship_id']: r['status'] for r in app_rows}

        # If sorted by recommendation score
        if sort_by == 'recommended':
            raw_results.sort(key=lambda x: x.get('match_score', 0), reverse=True)

    # Pagination slicing
    total_pages = max(1, (total_count + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paged_results = raw_results[start_idx:end_idx]

    # Available categories for filter dropdown
    categories = [r['category'] for r in query_db("SELECT DISTINCT category FROM internships WHERE is_active = 1 ORDER BY category ASC")]

    return render_template(
        'internships.html',
        internships=paged_results,
        categories=categories,
        total_count=total_count,
        page=page,
        total_pages=total_pages,
        q=q,
        category=category,
        work_mode=work_mode,
        stipend_type=stipend_type,
        location=location,
        sort_by=sort_by,
        user_saved_ids=user_saved_ids,
        user_app_map=user_app_map
    )


@app.route('/internships/<int:internship_id>')
def internship_detail(internship_id):
    """Detailed view for a single internship with matching breakdown and application options."""
    internship = query_db("SELECT * FROM internships WHERE id = ? AND is_active = 1", (internship_id,), one=True)
    if not internship:
        abort(404)

    internship_dict = dict(internship)
    match_details = None
    is_saved = False
    existing_app = None

    if session.get('user_id') and session.get('role') == 'student':
        uid = session['user_id']
        profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (uid,), one=True)
        if profile:
            match_details = RuleBasedRecommendationEngine.calculate_match(dict(profile), internship_dict)
            internship_dict['match_details'] = match_details

        saved_row = query_db("SELECT id FROM saved_internships WHERE user_id = ? AND internship_id = ?", (uid, internship_id), one=True)
        is_saved = bool(saved_row)

        existing_app = query_db("SELECT * FROM applications WHERE user_id = ? AND internship_id = ?", (uid, internship_id), one=True)

    # Similar internships in same category
    similar = query_db("""
        SELECT * FROM internships 
        WHERE category = ? AND id != ? AND is_active = 1 
        ORDER BY posted_date DESC 
        LIMIT 3
    """, (internship['category'], internship_id))

    return render_template(
        'internship_detail.html',
        internship=internship_dict,
        match_details=match_details,
        is_saved=is_saved,
        existing_app=existing_app,
        similar=similar
    )


# ==========================================
# Saved Internships Routes
# ==========================================

@app.route('/internships/<int:internship_id>/save', methods=['POST'])
@login_required
def toggle_save_internship(internship_id):
    """Saves or unsaves an internship for the logged-in student."""
    user_id = session['user_id']

    internship = query_db("SELECT id FROM internships WHERE id = ?", (internship_id,), one=True)
    if not internship:
        abort(404)

    saved = query_db("SELECT id FROM saved_internships WHERE user_id = ? AND internship_id = ?", (user_id, internship_id), one=True)

    if saved:
        execute_db("DELETE FROM saved_internships WHERE id = ?", (saved['id'],))
        action = "removed"
        flash("Internship removed from your saved list.", "info")
    else:
        execute_db("INSERT INTO saved_internships (user_id, internship_id) VALUES (?, ?)", (user_id, internship_id))
        action = "saved"
        flash("Internship successfully saved to your bookmarks!", "success")

    # If request is AJAX/fetch
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'status': 'ok', 'action': action})

    return redirect(request.referrer or url_for('saved_internships'))


@app.route('/saved-internships')
@login_required
def saved_internships():
    """View all saved internships for the logged-in student."""
    user_id = session['user_id']
    saved_rows = query_db("""
        SELECT i.*, s.saved_at
        FROM saved_internships s
        JOIN internships i ON s.internship_id = i.id
        WHERE s.user_id = ? AND i.is_active = 1
        ORDER BY s.saved_at DESC
    """, (user_id,))

    internships_list = [dict(r) for r in saved_rows]
    profile = query_db("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,), one=True)
    if profile:
        internships_list = RuleBasedRecommendationEngine.rank_internships(dict(profile), internships_list)

    return render_template('saved_internships.html', internships=internships_list)


# ==========================================
# Applications & Tracking Routes
# ==========================================

@app.route('/applications', methods=['GET', 'POST'])
@login_required
def applications():
    """Application tracker: list, record intention, confirm external application, and update status."""
    user_id = session['user_id']

    if request.method == 'POST':
        internship_id = request.form.get('internship_id', type=int)
        status = request.form.get('status', 'Interested').strip()
        notes = request.form.get('notes', '').strip()

        valid_statuses = {'Interested', 'Applied', 'Interview', 'Offered', 'Rejected', 'Withdrawn'}
        if status not in valid_statuses:
            flash("Invalid application status.", "danger")
            return redirect(url_for('applications'))

        internship = query_db("SELECT id, title, company FROM internships WHERE id = ?", (internship_id,), one=True)
        if not internship:
            abort(404)

        # Check existing application
        existing = query_db("SELECT id FROM applications WHERE user_id = ? AND internship_id = ?", (user_id, internship_id), one=True)
        if existing:
            execute_db("""
                UPDATE applications SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
            """, (status, notes, existing['id'], user_id))
            flash(f"Application status for {internship['title']} updated to '{status}'.", "success")
        else:
            execute_db("""
                INSERT INTO applications (user_id, internship_id, status, notes)
                VALUES (?, ?, ?, ?)
            """, (user_id, internship_id, status, notes))
            flash(f"Application record for {internship['title']} created as '{status}'.", "success")

        return redirect(request.referrer or url_for('applications'))

    # GET filter
    filter_status = request.args.get('status', '').strip()
    if filter_status:
        apps = query_db("""
            SELECT a.*, i.title, i.company, i.location, i.category, i.stipend, i.application_url
            FROM applications a
            JOIN internships i ON a.internship_id = i.id
            WHERE a.user_id = ? AND a.status = ?
            ORDER BY a.updated_at DESC
        """, (user_id, filter_status))
    else:
        apps = query_db("""
            SELECT a.*, i.title, i.company, i.location, i.category, i.stipend, i.application_url
            FROM applications a
            JOIN internships i ON a.internship_id = i.id
            WHERE a.user_id = ?
            ORDER BY a.updated_at DESC
        """, (user_id,))

    # Counts by status
    status_counts = {}
    for st in ['Interested', 'Applied', 'Interview', 'Offered', 'Rejected', 'Withdrawn']:
        c = query_db("SELECT COUNT(*) as c FROM applications WHERE user_id = ? AND status = ?", (user_id, st), one=True)['c']
        status_counts[st] = c

    return render_template(
        'applications.html',
        applications=apps,
        status_counts=status_counts,
        current_filter=filter_status
    )


@app.route('/applications/<int:app_id>/update', methods=['POST'])
@login_required
def update_application(app_id):
    """Enforces strict ownership check before updating application status or private notes."""
    user_id = session['user_id']
    status = request.form.get('status', '').strip()
    notes = request.form.get('notes', '').strip()

    valid_statuses = {'Interested', 'Applied', 'Interview', 'Offered', 'Rejected', 'Withdrawn'}
    if status not in valid_statuses:
        flash("Invalid status selected.", "danger")
        return redirect(url_for('applications'))

    # Verify ownership
    app_record = query_db("SELECT id, user_id FROM applications WHERE id = ?", (app_id,), one=True)
    if not app_record or app_record['user_id'] != user_id:
        abort(403)

    execute_db("""
        UPDATE applications 
        SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ?
    """, (status, notes, app_id, user_id))

    flash("Application record successfully updated.", "success")
    return redirect(url_for('applications'))


# ==========================================
# Admin Portal Routes
# ==========================================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with high-level statistics and recent internship management."""
    total_internships = query_db("SELECT COUNT(*) as c FROM internships", one=True)['c']
    total_students = query_db("SELECT COUNT(*) as c FROM users WHERE role = 'student'", one=True)['c']
    total_applications = query_db("SELECT COUNT(*) as c FROM applications", one=True)['c']
    total_saved = query_db("SELECT COUNT(*) as c FROM saved_internships", one=True)['c']

    # Application status distribution for Chart.js
    status_data = query_db("""
        SELECT status, COUNT(*) as count 
        FROM applications 
        GROUP BY status
    """)
    status_distribution = {r['status']: r['count'] for r in status_data}

    # Category distribution for Chart.js
    category_data = query_db("""
        SELECT category, COUNT(*) as count 
        FROM internships 
        GROUP BY category
    """)
    category_distribution = {r['category']: r['count'] for r in category_data}

    # All internships for management table
    internships_list = query_db("SELECT * FROM internships ORDER BY posted_date DESC")

    return render_template(
        'admin_dashboard.html',
        total_internships=total_internships,
        total_students=total_students,
        total_applications=total_applications,
        total_saved=total_saved,
        status_distribution=status_distribution,
        category_distribution=category_distribution,
        internships=internships_list
    )


@app.route('/admin/internships/add', methods=['GET', 'POST'])
@admin_required
def add_internship():
    """Admin route to create a new internship listing."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        company = request.form.get('company', '').strip()
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        work_mode = request.form.get('work_mode', 'Remote').strip()
        duration = request.form.get('duration', '').strip()
        stipend = request.form.get('stipend', '').strip()
        is_paid = 1 if request.form.get('is_paid') == '1' else 0
        required_skills = request.form.get('required_skills', '').strip()
        description = request.form.get('description', '').strip()
        eligibility = request.form.get('eligibility', '').strip()
        application_deadline = request.form.get('application_deadline', '').strip() or None
        application_url = request.form.get('application_url', '').strip()
        logo_url = request.form.get('logo_url', '').strip()

        # Validation
        if not title or not company or not category or not location or not required_skills or not description:
            flash("Please fill in all required fields marked with *.", "danger")
            return render_template('add_internship.html', form=request.form)

        execute_db("""
            INSERT INTO internships (
                title, company, logo_url, description, required_skills,
                category, location, work_mode, duration, stipend,
                is_paid, application_deadline, eligibility, application_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, company, logo_url, description, required_skills,
            category, location, work_mode, duration, stipend,
            is_paid, application_deadline, eligibility, application_url
        ))

        flash(f"Internship '{title}' successfully published!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('add_internship.html')


@app.route('/admin/internships/<int:internship_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_internship(internship_id):
    """Admin route to modify an existing internship listing."""
    internship = query_db("SELECT * FROM internships WHERE id = ?", (internship_id,), one=True)
    if not internship:
        abort(404)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        company = request.form.get('company', '').strip()
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        work_mode = request.form.get('work_mode', 'Remote').strip()
        duration = request.form.get('duration', '').strip()
        stipend = request.form.get('stipend', '').strip()
        is_paid = 1 if request.form.get('is_paid') == '1' else 0
        required_skills = request.form.get('required_skills', '').strip()
        description = request.form.get('description', '').strip()
        eligibility = request.form.get('eligibility', '').strip()
        application_deadline = request.form.get('application_deadline', '').strip() or None
        application_url = request.form.get('application_url', '').strip()
        logo_url = request.form.get('logo_url', '').strip()
        is_active = 1 if request.form.get('is_active') == '1' else 0

        if not title or not company or not category or not location or not required_skills or not description:
            flash("Please fill in all required fields marked with *.", "danger")
            return render_template('edit_internship.html', internship=internship)

        execute_db("""
            UPDATE internships SET
                title = ?, company = ?, logo_url = ?, description = ?,
                required_skills = ?, category = ?, location = ?, work_mode = ?,
                duration = ?, stipend = ?, is_paid = ?, application_deadline = ?,
                eligibility = ?, application_url = ?, is_active = ?
            WHERE id = ?
        """, (
            title, company, logo_url, description,
            required_skills, category, location, work_mode,
            duration, stipend, is_paid, application_deadline,
            eligibility, application_url, is_active,
            internship_id
        ))

        flash(f"Internship '{title}' has been successfully updated.", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_internship.html', internship=internship)


@app.route('/admin/internships/<int:internship_id>/delete', methods=['POST'])
@admin_required
def delete_internship(internship_id):
    """Admin route to delete an internship with confirmation."""
    internship = query_db("SELECT id, title FROM internships WHERE id = ?", (internship_id,), one=True)
    if not internship:
        abort(404)

    execute_db("DELETE FROM internships WHERE id = ?", (internship_id,))
    flash(f"Internship '{internship['title']}' was deleted.", "info")
    return redirect(url_for('admin_dashboard'))


# ==========================================
# Error Handlers
# ==========================================

@app.errorhandler(400)
def bad_request_error(e):
    return render_template('403.html', title="400 - Bad Request", message=str(e.description if hasattr(e, 'description') else "Bad Request")), 400

@app.errorhandler(403)
def forbidden_error(e):
    return render_template('403.html', title="403 - Access Forbidden", message="You do not have permission to access this resource."), 403

@app.errorhandler(404)
def not_found_error(e):
    return render_template('404.html', title="404 - Page Not Found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', title="500 - Server Error"), 500


if __name__ == '__main__':
    # Local development server
    port = int(os.environ.get('PORT', 5000))
    app.run(host='127.0.0.1', port=port, debug=True)
