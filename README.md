# InternSpark ⚡

InternSpark is a modern, responsive, and privacy-conscious web application designed for students and early-career professionals to discover tech internships through transparent, rule-based matching. Built with Python Flask, vanilla modern CSS/JS, and SQLite, it runs 100% locally with zero paid API keys or external machine learning dependencies.

---

## 🌟 Highlights & Key Features

- **Vibrant, Modern Aesthetics**: Curated color palette with purple (`#6366f1`), electric blue (`#0284c7`), coral (`#f97316`), and soft pink (`#ec4899`). Subtle drop shadows, glassmorphism navigation, rounded cards, and smooth CSS hover transitions.
- **Transparent Recommendation Engine**:
  - **70% Weight**: Overlap between student technical skills and internship required skills (with normalization and synonym recognition).
  - **30% Weight**: Match between student career interests and the internship domain/category.
  - **Plain-English Rationale**: Explains why a role is recommended (e.g., *"Matches 3 of 4 required skills (Python, SQL, Flask) + Category matches your interest in AI/ML"*).
- **Comprehensive Student Profile**:
  - Academic details, semester, graduation year, skills assistant with click-to-add chips, work mode preference (Remote, Hybrid, On-site), and bio.
  - **Secure Resume Upload**: Restricts uploads strictly to `.pdf` and `.docx` under 5MB. Files are saved with randomized collision-resistant names in a non-executable directory and served via an authenticated owner-only route (`/profile/resume/download`).
- **Full-Featured Search & Combined Filtering**:
  - Search by keywords (title, company, category, skill).
  - Filter by category, work mode, and paid/unpaid compensation.
  - Sort by newest, application deadline, stipend, or recommendation score.
  - Pagination and quick "Clear Filters" reset button.
- **Application Tracker & Bookmarking**:
  - Bookmark roles with instant AJAX toggling.
  - Track applications across 6 stages: `Interested`, `Applied`, `Interview`, `Offered`, `Rejected`, `Withdrawn`.
  - Add private reflection notes and interview logs.
- **Protected Administrator Portal**:
  - Role-based server-side authorization (`@admin_required`).
  - Add, edit, and delete internships with confirmation.
  - Visual analytics with Chart.js showing application pipeline distributions and platform counts.
- **Enterprise-Grade Security Practices**:
  - Werkzeug secure password hashing (`generate_password_hash`, `check_password_hash`).
  - Session-based CSRF protection tokens on all POST/PUT/DELETE forms.
  - Parameterized SQLite queries to prevent SQL injection.
  - Custom branded 403, 404, and 500 error pages.

---

## 📂 Project Directory Structure

```text
Internship finder website/
│
├── app.py                      # Core Flask application, routes, auth & security handlers
├── config.py                   # Configuration classes (Development, Testing, Production)
├── recommendation_engine.py    # Modular 70/30 rule-based recommendation engine
├── schema.sql                  # Database schema (users, profiles, internships, saves, apps)
├── seed.py                     # Database initialization and demo accounts/listings seed script
├── requirements.txt            # Python dependencies (Flask, Werkzeug, python-dotenv, pytest)
├── .env.example                # Template for environment configuration
├── .gitignore                  # Git ignore rules for venv, database files, and uploaded resumes
├── README.md                   # Setup documentation and user manual
│
├── static/
│   ├── css/
│   │   └── style.css           # Premium design system and component styling
│   ├── js/
│   │   ├── main.js             # Mobile menu, modals, alerts, and bookmark toggling
│   │   ├── dashboard.js        # Chart.js visualization logic
│   │   ├── profile.js          # File size checks and skill chips helper
│   │   └── internships.js      # Modal autofill and search helpers
│   ├── images/
│   └── uploads/                # Safe folder for uploaded student resumes
│
├── templates/
│   ├── base.html               # Master layout with responsive navbar, flash alerts, and footer
│   ├── index.html              # Landing page with hero, search, stats, and how-it-works
│   ├── register.html           # Student registration page
│   ├── login.html              # Login page with demo credentials quick-fill
│   ├── dashboard.html          # Student dashboard with completion meter and recommendations
│   ├── profile.html            # Profile editor with resume upload and skill chips
│   ├── internships.html        # Search and filtering catalogue
│   ├── internship_detail.html  # Detailed role specifications with match score breakdown
│   ├── saved_internships.html  # Bookmarked internships
│   ├── applications.html       # Status tracker with private notes
│   ├── admin_dashboard.html    # Admin management panel and metrics
│   ├── add_internship.html     # Admin add listing form
│   ├── edit_internship.html    # Admin edit listing form
│   ├── 403.html                # Access forbidden error page
│   ├── 404.html                # Page not found error page
│   └── 500.html                # Internal server error page
│
└── tests/
    └── test_app.py             # 19 automated tests running on an isolated test database
```

---

## 🛠️ Step-by-Step Windows PowerShell Setup

Follow these exact commands in Windows PowerShell:

### 1. Open Project in Terminal
Open your project directory in PowerShell:
```powershell
cd "c:\Users\Ramte\OneDrive\Desktop\Internship finder website"
```

### 2. Create and Activate a Python Virtual Environment
A virtual environment isolates dependencies from your system Python.
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell displays an execution policy error, enable local script execution with: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

### 3. Install Dependencies
Install all required packages specified in `requirements.txt`:
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to create your local `.env` configuration file:
```powershell
Copy-Item .env.example .env
```

### 5. Initialize Database & Seed Demo Data
Run `seed.py` to create the SQLite database tables and seed sample accounts and tech listings:
```powershell
python seed.py --reset
```

#### Demo Credentials (Local Development):
- **Student Account**:
  - Email: `student@internspark.demo`
  - Password: `Student@12345`
  - *(Pre-seeded with college info, skills in Python, Flask, React, and ML for instant recommendations)*
- **Admin Account**:
  - Email: `admin@internspark.demo`
  - Password: `Admin@Secure2026`

### 6. Run the Application
Start the local Flask development server:
```powershell
python app.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Running Automated Tests

InternSpark includes 19 comprehensive unit and integration tests executed on an **isolated temporary database** so your development data is never altered:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```

### Verified Test Cases (19/19 Passed):
1. `test_home_page_loads`: Verified HTTP 200 and presence of hero elements and stats.
2. `test_registration_works`: Verified account creation, validation, and session setup.
3. `test_duplicate_registration_rejected`: Verified rejection of duplicate email registration.
4. `test_passwords_are_hashed`: Verified Werkzeug password hashing verification.
5. `test_invalid_login_rejected`: Verified rejection of incorrect credentials.
6. `test_valid_login_works`: Verified successful login and session establishment.
7. `test_logout_clears_session`: Verified session clearing on logout.
8. `test_private_pages_require_auth`: Verified redirect to `/login` for unauthenticated requests.
9. `test_internship_search`: Verified keyword querying against titles and skills.
10. `test_combined_filters`: Verified filtering by category, work mode, and stipend type.
11. `test_profile_updates_persist`: Verified profile editing persists accurately in SQLite.
12. `test_recommendation_engine_scoring`: Verified 70% skill / 30% interest rule mathematics.
13. `test_save_unsave_internship`: Verified bookmarking and un-bookmarking operations.
14. `test_application_ownership_enforcement`: Verified strict 403 Forbidden when accessing another user's record.
15. `test_application_creation_and_update`: Verified updating status stages and private notes.
16. `test_admin_route_protection`: Verified 403 Forbidden for non-admin accounts accessing `/admin`.
17. `test_admin_create_and_edit_internship`: Verified admin CRUD operations on internships.
18. `test_invalid_resume_upload_rejected`: Verified rejection of unsafe file types (e.g., `.exe`).
19. `test_404_error_page`: Verified custom branded 404 handler for missing routes.

---

## 🔒 Security Best Practices & Production Deployment

Before deploying InternSpark to a public production environment:
1. **Secret Key**: Generate a cryptographically secure 32-byte secret key and store it in `.env` (`SECRET_KEY=...`).
2. **HTTPS & Cookies**: In `config.py`, enable `SESSION_COOKIE_SECURE = True` so cookies are only transmitted over TLS/SSL.
3. **Production WSGI Server**: Do not use the Flask built-in server (`app.run`) in production. Use a production WSGI server such as **Gunicorn** or **Waitress** (on Windows):
   ```powershell
   pip install waitress
   waitress-serve --port=5000 app:app
   ```
4. **File Storage**: Ensure the `uploads/` directory has non-executable file permissions and is served exclusively through the authenticated Flask route (`/profile/resume/download`).
5. **Change Default Passwords**: Immediately reset demo student and admin credentials before any public access.
