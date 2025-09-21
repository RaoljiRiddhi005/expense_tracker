# Copilot Instructions for expense_tracker

## Project Overview
- **Framework:** Flask (see `run.py`, `app/`)
- **Purpose:** Web-based expense tracker with user registration, login, and dashboard.
- **Persistence:** MySQL via SQLAlchemy ORM (see `config.py`, `app/models.py`)
- **Templates:** Jinja2 HTML templates in `templates/`

## Architecture
- `run.py`: App entry point, creates Flask app, registers blueprints, sets up DB and migrations.
- `app/`
  - `routes.py`: All Flask routes (register, login, dashboard, etc.) via a single blueprint (`bp`).
  - `models.py`: SQLAlchemy models (currently only `User`).
  - `extensions.py`: Initializes Flask extensions (e.g., `db`).
- `config.py`: Loads environment variables and configures Flask/SQLAlchemy.
- `requirements.txt`: All dependencies are pinned.

## Key Patterns & Conventions
- **Blueprints:** All routes are registered under a single blueprint (`bp` in `routes.py`).
- **User Auth:** Passwords are hashed using Werkzeug. User model provides `set_password` and `check_password` methods.
- **Environment:** Secrets and DB credentials are loaded from a `.env` file (see `config.py`).
- **Migrations:** Use Flask-Migrate for DB schema changes.
- **Templates:** Use Jinja2 for rendering HTML. Template files are in `templates/`.
- **Flash Messages:** Use Flask's `flash()` for user feedback.

## Developer Workflows
- **Run App (dev):**
  ```powershell
  python run.py
  ```
- **DB Migration:**
  ```powershell
  flask db init   # (first time only)
  flask db migrate -m "message"
  flask db upgrade
  ```
- **Install Requirements:**
  ```powershell
  pip install -r requirements.txt
  ```

## Integration Points
- **Database:** MySQL (see `config.py` for URI format)
- **Environment:** Requires `.env` file with DB credentials and `SECRET_KEY`

## Project-Specific Notes
- All business logic is in `routes.py` (no service layer abstraction).
- No API endpoints (all server-rendered HTML).
- No frontend JS framework; all interactivity is server-side.

## Example: Adding a New Route
1. Add a function in `app/routes.py` decorated with `@bp.route("/yourpath")`.
2. Add a corresponding template in `templates/` if needed.
3. Use `render_template()` to render HTML.

---

**For AI agents:**
- Follow the patterns in `routes.py` for new features.
- Use SQLAlchemy models from `models.py` for DB access.
- Always hash passwords using `User.set_password()`.
- Reference `config.py` for any config/environment needs.
