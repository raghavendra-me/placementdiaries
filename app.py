from flask import Flask, flash, request, render_template, redirect, url_for, session, jsonify, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
import joblib
import re
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# MongoDB configuration
MONGO_URI = 'mongodb+srv://Raghu:zjQnWPOKq8Quyo3h@cluster0.tvkq752.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(MONGO_URI)
db = client['PlacementDiaries']
users_collection = db['users']
journeys_collection = db['journeys']

# Load model and vectorizer
model = joblib.load('random_forest_model.pkl')
vectorizer = joblib.load('tfidf_vectorizer.pkl')
POOR_SKILLS = ["ms office", "finance", "basic computer knowledge", "management", "word", "ppt", "mongo", "powerpoint", "excel", "tableau", "power bi"]
IMPORTANT_TOOLS = ["agile", "jira", "scrum", "trello", "kanban", "confluence"]

# Job role mappings for specific skills and tools
ROLE_MAPPINGS = {
    "elixir": "Cloud Services Developer",
    "c": "Low-Level Software Engineer",
    "prompt_engineering": "Machine Learning Engineer (NLP Specialization)",
    "linux": "Security Operations Engineer",
    "swift": "App Developer",
    "vue.js": "UI Developer (SPA Specialization)",
    "agile": "Project Manager",
    "jira": "Scrum Master",
    "scrum": "Agile Coach",
    "trello": "Project Coordinator",
    "kanban": "Agile Coach",
    "confluence": "Product Manager"
}

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Check if username or email already exists
        if users_collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            flash('Username or email already exists')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert the new user
        users_collection.insert_one({
            'username': username,
            'password': hashed_password,
            'email': email
        })

        flash('Registration successful. Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = users_collection.find_one({'username': username})

        if user and check_password_hash(user['password'], password):
            session['logged_in'] = True
            session['username'] = username
            flash('Logged in successfully.')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/home')
def home():
    if 'logged_in' in session and session['logged_in']:
        return render_template('home.html', username=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/job_role')
def job_role():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return render_template('job_role.html')

@app.route('/share', methods=['GET', 'POST'])
def share_journey():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))

    if request.method == 'POST':
        journey = {
            'year': request.form['year'],
            'company': request.form['company'],
            'name': request.form['name'],
            'email': request.form['email'],
            'gender': request.form['gender'],
            'skills': request.form['skills'],
            'salary': request.form['salary'],
            'jobrole': request.form['jobrole'],
            'projects': request.form['projects'],
            'suggestions': request.form['suggestions'],
            'username': session['username']
        }
        try:
            journeys_collection.insert_one(journey)
            flash('Journey shared successfully.')
        except Exception as e:
            flash(f"An error occurred while saving: {e}")
        return redirect(url_for('view_journey'))
    return render_template('share_journey.html')

@app.route('/view_others')
def view_journey():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    journeys = list(journeys_collection.find())
    return render_template('view_journey.html', journeys=journeys)

@app.route('/upload_skills')
def upload_skills():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'error': 'Not logged in'}), 401

    skills = request.form['Skills'].lower()
    skills_list = re.split(r'\W+', skills)

    for skill, role in ROLE_MAPPINGS.items():
        if skill in skills_list:
            session['predicted_role'] = role
            return jsonify({'prediction': role})

    if "java" in skills_list:
        predicted_role = "Java Developer"
        session['predicted_role'] = predicted_role
        return jsonify({'prediction': predicted_role})

    filtered_skills = " ".join(skill for skill in skills_list if skill not in POOR_SKILLS or skill in IMPORTANT_TOOLS)
    
    if not filtered_skills.strip():
        return jsonify({'prediction': "Please add more specific skills relevant to the job role."})
    
    input_data = vectorizer.transform([filtered_skills]).toarray()
    predicted_role = model.predict(input_data)[0]
    if predicted_role == "Mobile App Developer":
        return jsonify({'prediction': "The skills provided may not match a specific role. Please add more relevant skills to improve the prediction."})
    
    session['predicted_role'] = predicted_role
    return jsonify({'prediction': predicted_role})

@app.route('/get_predicted_role')
def get_predicted_role():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({'error': 'Not logged in'}), 401
    predicted_role = session.get('predicted_role', None)
    return jsonify({'predicted_role': predicted_role})

if __name__ == '__main__':
    app.run(debug=True)