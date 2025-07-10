from functools import wraps
from dashboard import create_dash_app as create_dashboard_app
from sales_analysis import create_dash_app as create_sales_analysis_app
from customer_insights import create_dash_app as create_customer_insights_app
from geo_forecast import create_dash_app as create_geo_forecast_app
from category_predictions import create_dash_app as create_category_predictions_app
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
bcrypt = Bcrypt(app)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client.product_demand_forecast
users_collection = db.users


# Mount Dash apps
dashboard_app = create_dashboard_app(app)               # Mounted at /dashboard/
sales_analysis_app = create_sales_analysis_app(app)     # Mounted at /sales/
customer_insights_app = create_customer_insights_app(app)  # Mounted at /customer/
geo_forecast_app = create_geo_forecast_app(app)         # Mounted at /geo_forecast/
category_predictions_app = create_category_predictions_app(app)  # Mounted at /category/

# Home route – Protected

# Optional: login_required decorator to protect routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
@login_required
def home():
    if 'email' in session:
        return render_template('index.html', email=session['email'], role=session['role'])
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email'].lower()
        password = request.form['password']
        role = request.form['role']

        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('signup'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role
        }

        users_collection.insert_one(new_user)
        flash('Registration successful. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').lower().strip()
        password = request.form.get('password', '')

        user = users_collection.find_one({'email': email})

        if user and bcrypt.check_password_hash(user['password'], password):
            session['email'] = user['email']
            session['role'] = user['role']
            flash('Login successful.', 'success')
            # Render index.html with user info after login
            return render_template('index.html', email=user['email'], role=user['role'])
        else:
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
