from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint("main", __name__)

# ---------------- INDEX ----------------
@bp.route("/")
def index():
    return render_template("index.html")

# ---------------- REGISTER ----------------
@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        # ✅ Validation checks
        if not username or not email or not password:
            flash("All fields are required!", "danger")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return render_template("register.html")

        if User.query.filter_by(username=username).first():
            flash("Username is already taken!", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("Email is already registered!", "danger")
            return render_template("register.html")

        # ✅ Create new user
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("main.login"))

    return render_template("register.html")

# ---------------- LOGIN ----------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"].strip()

        if not email or not password:
            flash("Email and password are required!", "danger")
            return render_template("login.html")

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("User not found. Please register first!", "warning")
            return redirect(url_for("main.register"))

        if not check_password_hash(user.password_hash, password):
            flash("Invalid email or password!", "danger")
            return render_template("login.html")

        # ✅ Store user session
        session["user_id"] = user.id
        session["username"] = user.username
        flash("Login successful!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please login first!", "warning")
        return redirect(url_for("main.login"))
    return render_template("dashboard.html", username=session["username"])

# ---------------- LOGOUT ----------------
@bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
