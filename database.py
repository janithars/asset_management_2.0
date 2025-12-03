# database.py
from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_login import UserMixin
from sqlalchemy import inspect, text

app = Flask(__name__)

# Secret key for session management
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Connect to SQL Server 2022 (Windows Authentication)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "mssql+pyodbc://@JANITH-PC\\SQLEXPRESS/AssetDB?"
    "driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&Encrypt=no"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------- MODELS -----------------


class User(db.Model, UserMixin):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Employee(db.Model):
    __tablename__ = 'Employee'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)

    # Relationship - one employee can have many assets
    assets = db.relationship('Asset', backref='employee', lazy=True)


class Asset(db.Model):
    __tablename__ = 'Asset'
    id = db.Column(db.Integer, primary_key=True)
    asset_type = db.Column(db.String(50), nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50))
    part_no = db.Column(db.String(50))
    serial_no = db.Column(db.String(50))
    location = db.Column(db.String(100))
    status = db.Column(db.String(50), default='Active')
    employee_id = db.Column(
        db.Integer, db.ForeignKey('Employee.id'), nullable=True)


# ----------------- INITIALIZATION -----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('Asset')]

        # Add status column if missing
        if 'status' not in columns:
            db.session.execute(
                text("ALTER TABLE Asset ADD status VARCHAR(50)"))
            db.session.commit()
            print("✅ Added 'status' column to Asset.")

        # Add employee_id column if missing
        if 'employee_id' not in columns:
            db.session.execute(
                text("ALTER TABLE Asset ADD employee_id INT NULL"))
            db.session.commit()
            print("✅ Added 'employee_id' column to Asset.")

        print("✅ Database initialized and tables ensured.")
