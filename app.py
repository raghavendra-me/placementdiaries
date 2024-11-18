from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
import joblib
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Hardcoded login credentials
USERNAME = 'admin'
PASSWORD = 'password123'

# MongoDB configuration
MONGO_URI = 'mongodb+srv://Raghu:zjQnWPOKq8Quyo3h@cluster0.tvkq752.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(MONGO_URI)
db = client['PlacementDiaries']
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

# Login route
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/job_role')
def job_role():
    return render_template('job_role.html')

@app.route('/login', methods=['POST'])
def login_submit():
    username = request.form['username']
    password = request.form['password']
    if username == USERNAME and password == PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('home'))
    else:
        error = "Invalid username or password"
        return render_template('login.html', error=error)

@app.route('/home')
def home():
    if 'logged_in' in session and session['logged_in']:
        return render_template('home.html')
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/share', methods=['GET', 'POST'])
def share_journey():
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
            'suggestions': request.form['suggestions']
        }
        try:
            journeys_collection.insert_one(journey)
        except Exception as e:
            return f"An error occurred while saving: {e}"
        return redirect(url_for('view_journey'))
    return render_template('share_journey.html')

@app.route('/view_others')
def view_journey():
    journeys = list(journeys_collection.find())
    return render_template('view_journey.html', journeys=journeys)

@app.route('/upload_skills')
def upload_skills():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    skills = request.form['Skills'].lower()
    skills_list = re.split(r'\W+', skills)

    # Check for specific skill and tool mappings to job roles
    for skill, role in ROLE_MAPPINGS.items():
        if skill in skills_list:
            session['predicted_role'] = role
            return jsonify({'prediction': role})

    # Directly predict "Java Developer" if the skill "java" is in the input
    if "java" in skills_list:
        predicted_role = "Java Developer"
        session['predicted_role'] = predicted_role
        return jsonify({'prediction': predicted_role})

    # Filter out poor skills and retain important tools
    filtered_skills = " ".join(skill for skill in skills_list if skill not in POOR_SKILLS or skill in IMPORTANT_TOOLS)
    
    if not filtered_skills.strip():
        return jsonify({'prediction': "Please add more specific skills relevant to the job role."})
    
    # Proceed with model prediction if no predefined role was matched
    input_data = vectorizer.transform([filtered_skills]).toarray()
    predicted_role = model.predict(input_data)[0]
    if predicted_role == "Mobile App Developer":
        return jsonify({'prediction': "The skills provided may not match a specific role. Please add more relevant skills to improve the prediction."})
    
    # Store prediction in session for later use
    session['predicted_role'] = predicted_role
    return jsonify({'prediction': predicted_role})

@app.route('/get_predicted_role')
def get_predicted_role():
    predicted_role = session.get('predicted_role', None)
    return jsonify({'predicted_role': predicted_role})

if __name__ == '__main__':
    app.run(debug=True)

# This code block is for demonstration purposes only and won't execute in this environment.
print("This is a Python Flask application converted to use MongoDB.")