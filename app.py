# App.py
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import db, Asset, User, Employee, app as db_app
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from sqlalchemy import inspect, text


def add_column(table_name, column_name, column_type):
    """
    Dynamically adds a column to an existing SQL table.
    """
    try:
        with db.engine.connect() as conn:
            conn.execute(
                text(
                    f'ALTER TABLE [{table_name}] ADD [{column_name}] {column_type}')
            )
            conn.commit()
        return True
    except Exception as e:
        print(f"Error adding column: {e}")
        return False


app = db_app
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Ensure tables exist
with app.app_context():
    db.create_all()

# ---------------- AUTH ROUTES ----------------


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Try another.', 'danger')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/employees', methods=['GET', 'POST'])
@login_required
def employees():
    if request.method == 'POST':
        name = request.form['name']
        department = request.form['department']
        position = request.form['position']
        email = request.form['email']
        new_emp = Employee(name=name, department=department,
                           position=position, email=email)
        db.session.add(new_emp)
        db.session.commit()
        flash('Employee added successfully!', 'success')
        return redirect(url_for('employees'))
    all_employees = Employee.query.all()
    return render_template('employees.html', employees=all_employees)


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        keyword = request.form['keyword']

        # Join Asset and Employee and filter
        assets = Asset.query.outerjoin(Employee).options(joinedload(Asset.employee)).filter(
            or_(
                Asset.asset_type.contains(keyword),
                Asset.brand.contains(keyword),
                Asset.model.contains(keyword),
                Asset.part_no.contains(keyword),
                Asset.serial_no.contains(keyword),
                Asset.location.contains(keyword),
                Asset.status.contains(keyword),
                Employee.name.contains(keyword)  # search by employee name
            )
        ).all()
    else:
        assets = Asset.query.options(joinedload(Asset.employee)).all()

    return render_template('index.html', assets=assets, user=current_user)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_asset():
    employees = Employee.query.all()
    if request.method == 'POST':
        emp_id = request.form.get('employee_id') or None
        new_asset = Asset(
            asset_type=request.form['asset_type'],
            brand=request.form['brand'],
            model=request.form['model'],
            part_no=request.form['part_no'],
            serial_no=request.form['serial_no'],
            location=request.form['location'],
            status=request.form.get('status') or 'Active',
            employee_id=emp_id
        )
        db.session.add(new_asset)
        db.session.commit()
        flash('Asset added successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('add.html', employees=employees)


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_asset(id):
    asset = Asset.query.get_or_404(id)
    employees = Employee.query.all()
    if request.method == 'POST':
        asset.asset_type = request.form['asset_type']
        asset.brand = request.form['brand']
        asset.model = request.form['model']
        asset.part_no = request.form['part_no']
        asset.serial_no = request.form['serial_no']
        asset.location = request.form['location']
        asset.status = request.form.get('status') or 'Active'
        asset.employee_id = request.form.get('employee_id') or None
        db.session.commit()
        flash('Asset updated successfully!', 'success')
        return redirect(url_for('index'))
    return render_template('edit.html', asset=asset, employees=employees)


@app.route('/delete/<int:id>')
@login_required
def delete_asset(id):
    asset = Asset.query.get_or_404(id)
    db.session.delete(asset)
    db.session.commit()
    flash('Asset deleted.', 'info')
    return redirect(url_for('index'))


@app.route('/print')
@login_required
def print_assets():
    assets = Asset.query.all()
    return render_template('print.html', assets=assets)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)


@app.route('/manage_columns/<table>', methods=['GET', 'POST'])
@login_required
def manage_columns(table):
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table)]

    if request.method == 'POST':
        column_name = request.form['column_name']
        column_type = request.form['column_type']
        if add_column(table, column_name, column_type):
            flash(f'Column {column_name} added to {table}!', 'success')
        else:
            flash('Error adding column.', 'danger')
        return redirect(url_for('manage_columns', table=table))

    return render_template('manage_columns.html', table=table, columns=columns)


if __name__ == "__main__":
    app.run(debug=True)
