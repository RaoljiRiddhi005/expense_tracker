from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User, Income, Expense
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, date, timedelta
from calendar import monthrange

bp = Blueprint("main", __name__)

# ---------------- LOGIN REQUIRED DECORATOR ----------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first!", "warning")
            return redirect(url_for("main.login"))
        return f(*args, **kwargs)
    return decorated_function

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

        session["user_id"] = user.id
        session["username"] = user.username
        flash("Login successful!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html")

# ---------------- DASHBOARD ----------------
@bp.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]

    filter_type = request.args.get("filterType", "month")  # month/week/year
    year = int(request.args.get("year", datetime.now().year))
    month = request.args.get("month")
    week = request.args.get("week")
    today = date.today()

    incomes = []
    expenses = []

    # ---------- Year filter ----------
    if filter_type == "year":
        incomes = Income.query.filter(
            Income.user_id == user_id,
            db.extract("year", Income.received_on) == year
        ).all()
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            db.extract("year", Expense.transaction_date) == year
        ).all()

    # ---------- Month filter ----------
    elif filter_type == "month" and month:
        month = int(month)
        incomes = Income.query.filter(
            Income.user_id == user_id,
            db.extract("year", Income.received_on) == year,
            db.extract("month", Income.received_on) == month
        ).all()
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            db.extract("year", Expense.transaction_date) == year,
            db.extract("month", Expense.transaction_date) == month
        ).all()

    # ---------- Week filter ----------
    elif filter_type == "week" and month and week:
        month = int(month)
        week = int(week)

        first_day = date(year, month, 1)
        last_day = date(year, month, monthrange(year, month)[1])

        # split month into week ranges
        week_ranges = []
        start = first_day
        while start <= last_day:
            end = min(start + timedelta(days=6), last_day)
            week_ranges.append((start, end))
            start = end + timedelta(days=1)

        if week <= len(week_ranges):
            start_date, end_date = week_ranges[week - 1]
            incomes = Income.query.filter(
                Income.user_id == user_id,
                Income.received_on.between(start_date, end_date)
            ).all()
            expenses = Expense.query.filter(
                Expense.user_id == user_id,
                Expense.transaction_date.between(start_date, end_date)
            ).all()

    # ---------- Default (current month) ----------
    else:
        incomes = Income.query.filter(
            Income.user_id == user_id,
            db.extract("year", Income.received_on) == today.year,
            db.extract("month", Income.received_on) == today.month
        ).all()
        expenses = Expense.query.filter(
            Expense.user_id == user_id,
            db.extract("year", Expense.transaction_date) == today.year,
            db.extract("month", Expense.transaction_date) == today.month
        ).all()

    # Totals
    total_income = sum(float(i.income_amount) for i in incomes)
    total_expense = sum(float(e.expense_amount) for e in expenses)
    current_balance = total_income - total_expense

    # Merge transactions for table
    transactions = []
    for i in incomes:
        transactions.append({
            "type": "Income",
            "amount": i.income_amount,
            "source": i.source,
            "notes": i.notes,
            "received_via": i.received_via,
            "date": i.received_on
        })
    for e in expenses:
        transactions.append({
            "type": "Expense",
            "amount": e.expense_amount,
            "category": e.category,
            "description": e.description,
            "payment_mode": e.payment_mode,
            "date": e.transaction_date
        })

    # Sort by date (latest first)
    transactions.sort(key=lambda x: x["date"], reverse=True)

    return render_template(
        "dashboard.html",
        username=session["username"],
        total_income=total_income,
        total_expense=total_expense,
        current_balance=current_balance,
        transactions=transactions,
        filter_type=filter_type,
        year=year,
        month=month,
        week=week
    )

# ---------------- ADD INCOME ----------------
@bp.route("/add_income", methods=["GET", "POST"])
@login_required
def add_income():
    if request.method == "POST":
        try:
            income_amount = float(request.form["income_amount"])
        except ValueError:
            flash("Invalid income amount!", "danger")
            return redirect(url_for("main.add_income"))

        source = request.form["source"]
        notes = request.form.get("notes", "")
        received_via = request.form["received_via"]
        received_on = request.form["received_on"]

        new_income = Income(
            user_id=session["user_id"],
            income_amount=income_amount,
            source=source,
            notes=notes,
            received_via=received_via,
            received_on=received_on
        )
        db.session.add(new_income)
        db.session.commit()

        flash("Income added successfully!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_income.html")

# ---------------- ADD EXPENSE ----------------
@bp.route("/add_expense", methods=["GET", "POST"])
@login_required
def add_expense():
    if request.method == "POST":
        try:
            expense_amount = float(request.form["expense_amount"])
        except ValueError:
            flash("Invalid expense amount!", "danger")
            return redirect(url_for("main.add_expense"))

        category = request.form["category"]
        description = request.form.get("description", "")
        payment_mode = request.form["payment_mode"]
        transaction_date = request.form["transaction_date"]

        new_expense = Expense(
            user_id=session["user_id"],
            expense_amount=expense_amount,
            category=category,
            description=description,
            payment_mode=payment_mode,
            transaction_date=transaction_date
        )
        db.session.add(new_expense)
        db.session.commit()

        flash("Expense added successfully!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_expense.html")

# ---------------- LOGOUT ----------------
@bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))



# ---------------- USER TRANSACTIONS ----------------
@bp.route("/user_transactions")
@login_required
def user_transactions():
    user_id = session["user_id"]

    # Filters
    filter_type = request.args.get("filter_type", "all")  # all, income, expense
    time_filter = request.args.get("time_filter", "year")  # year, month, week
    sort = request.args.get("sort", "recent")  # recent, oldest
    year = int(request.args.get("year", datetime.now().year))
    month = int(request.args.get("month", 1))
    week = int(request.args.get("week", 1))

    # Get all incomes and expenses
    incomes = Income.query.filter_by(user_id=user_id).all()
    expenses = Expense.query.filter_by(user_id=user_id).all()

    # Merge transactions
    transactions = []
    for i in incomes:
        transactions.append({
            "type": "Income",
            "amount": i.income_amount,
            "source": i.source,
            "notes": i.notes,
            "received_via": i.received_via,
            "date": i.received_on
        })
    for e in expenses:
        transactions.append({
            "type": "Expense",
            "amount": e.expense_amount,
            "category": e.category,
            "description": e.description,
            "payment_mode": e.payment_mode,
            "date": e.transaction_date
        })

    # ---------- Apply type filter ----------
    if filter_type.lower() == "income":
        transactions = [t for t in transactions if t["type"].lower() == "income"]
    elif filter_type.lower() == "expense":
        transactions = [t for t in transactions if t["type"].lower() == "expense"]

    # ---------- Apply time filter ----------
    filtered = []
    for t in transactions:
        t_date = t["date"]
        if isinstance(t_date, str):
            t_date = datetime.strptime(t_date, "%Y-%m-%d").date()
        if time_filter == "year" and t_date.year == year:
            filtered.append(t)
        elif time_filter == "month" and t_date.year == year and t_date.month == month:
            filtered.append(t)
        elif time_filter == "week" and t_date.year == year and t_date.month == month:
            first_day = date(year, month, 1)
            last_day = date(year, month, monthrange(year, month)[1])
            # Compute week ranges
            week_ranges = []
            start = first_day
            while start <= last_day:
                end = min(start + timedelta(days=6), last_day)
                week_ranges.append((start, end))
                start = end + timedelta(days=1)
            if week <= len(week_ranges):
                start_date, end_date = week_ranges[week - 1]
                if start_date <= t_date <= end_date:
                    filtered.append(t)
    transactions = filtered

    # ---------- Sort ----------
    transactions.sort(key=lambda x: x["date"], reverse=(sort=="recent"))

    return render_template(
        "user_transactions.html",
        page="transactions",
        username=session["username"],
        transactions=transactions,
        filter_type=filter_type,
        time_filter=time_filter,
        sort=sort,
        year=year,
        month=month,
        week=week
    )

