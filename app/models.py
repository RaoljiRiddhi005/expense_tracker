from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

# ---------------- USER ----------------
class User(db.Model):
    __tablename__ = 'user'  # must match your MySQL table name

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ---------------- EXPENSE ----------------
class Expense(db.Model):
    __tablename__ = "expenses"

    expense_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    expense_amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    payment_mode = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)

    user = db.relationship("User", backref="expenses")

# ---------------- INCOME ----------------
class Income(db.Model):
    __tablename__ = "income"

    income_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    income_amount = db.Column(db.Float, nullable=False)
    source = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text)
    received_via = db.Column(db.String(50), nullable=False)
    received_on = db.Column(db.Date, nullable=False, default=date.today)

    user = db.relationship("User", backref="income")
