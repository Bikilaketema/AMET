import bcrypt
from flask import Flask, render_template, request, redirect, session
import requests
import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth
import json
import os

app = Flask(__name__, static_folder='static')
app.secret_key = 'your-secret-key'  # Add a secret key for session management

# Initialize Firebase Admin SDK
cred = credentials.Certificate('/home/bicky/AMET/app/serviceAccountKey.json')
firebase_admin.initialize_app(cred)

# Route to display the index.html template
@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/index')
def index():
    # Fetch product data from the FakeStore API
    response = requests.get('https://fakestoreapi.com/products')
    products = response.json()

    return render_template('index.html', products=products)

@app.route('/products')
def products():
    # Fetch product categories from the FakeStore API
    response = requests.get('https://fakestoreapi.com/products/categories')
    categories = response.json()

    return render_template('products.html', categories=categories)

@app.route('/category/<string:category>')
def category(category):
    url = f'https://fakestoreapi.com/products/category/{category}'
    response = requests.get(url)
    products = response.json()
    return render_template('category.html', category=category, products=products)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


""" # Function to fetch product details from the Fake Store API
def get_product_details(product_id):
    url = f'https://fakestoreapi.com/products/{product_id}'
    response = requests.get(url)
    
    if response.status_code == 200:
        product = response.json()
        return product
    else:
        return None

# Route for product detail page
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Retrieve product details from the Fake Store API
    product = get_product_details(product_id)

    if product is None:
        return render_template('404.html'), 404

    return render_template('product_detail.html', product=product) """



@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if len(password) < 6:
            # Password is too short
            return render_template('signup.html', error='Password must be at least 6 characters long.', email=email)

        if password == confirm_password:
            try:
                user = auth.create_user(email=email, password=password)
                session['user'] = user.uid  # Store the user ID in the session

                # Create a dictionary with user information
                user_data = {
                    'email': email,
                    'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                }

                file_path = 'users.json'

                # Check if the JSON file exists
                if not os.path.exists(file_path):
                    # Create the file if it doesn't exist
                    with open(file_path, 'w') as file:
                        json.dump([], file)

                # Read existing user data from the JSON file
                with open(file_path, 'r') as file:
                    data = json.load(file)

                # Add the new user data to the existing data
                data.append(user_data)

                # Write the updated JSON data
                with open(file_path, 'w') as file:
                    json.dump(data, file)

                return redirect('/dashboard')
            except auth.EmailAlreadyExistsError:
                # User with the given email already exists
                return render_template('signup.html', error='Email already exists.', email=email)
            except Exception as e:
                # Print error details for debugging
                print(f"Error during signup: {str(e)}")
                return render_template('signup.html', error='An error occurred during signup.', email=email)
        else:
            # Passwords do not match
            return render_template('signup.html', error='Passwords do not match.', email=email)

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            user = auth.get_user_by_email(email)
            uid = user.uid

            # Get the stored password from the JSON file
            with open('users.json', 'r') as file:
                user_data = json.load(file)
                stored_password = next((data['password'] for data in user_data if data['email'] == email), None)

            if stored_password is not None and bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8')):
                session['user'] = uid  # Store the user ID in the session
                return redirect('/dashboard')
            else:
                # Incorrect password
                return render_template('login.html', error='Incorrect password.', email=email)

        except auth.UserNotFoundError:
            # User with the given email doesn't exist
            return render_template('login.html', error='Account associated with this email not found. Click the signup button and create one.', email=email)
        except Exception as e:
            # Print error details for debugging
            print(f"Error during login: {str(e)}")
            return render_template('login.html', error='An error occurred during login.', email=email)

    return render_template('login.html')




@app.route('/dashboard')
def dashboard():
    user_id = session.get('user')
    if not user_id:
        return redirect('/login')

    # Get user data from Firebase
    user = auth.get_user(user_id)
    email = user.email
    return render_template('dashboard.html', email=email)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)