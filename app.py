from flask import Flask, jsonify, render_template, request, redirect, session, url_for, flash 
# import whisper
import docx
import PyPDF2
import requests
import os,re
from dotenv import load_dotenv
from flask_cors import CORS
import sqlite3
# from youtube_transcript_api import YouTubeTranscriptApi
import os
import subprocess
import json
import warnings


app = Flask(__name__, static_folder='.', static_url_path='')

CORS(app)
CORS(app, supports_credentials=True)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})
CORS(app, origins=["http://localhost:8000"])

load_dotenv()

# For Dev
app.secret_key = "adf703e0db6fbd77635a40638ad2018b"  # Needed for session and flash
ACCESS_TOKEN = 'AIzaSyDd-JR1M20_vGgCtf0LYCEy1p5YFsDy1ts'
warnings.filterwarnings("ignore", category=UserWarning)
# model = whisper.load_model("base")

# For Prod
# app.secret_key = os.getenv("FLASK_SECRET_KEY")
# ACCESS_TOKEN = os.getenv("GEMINI_API_KEY")

def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    # Add a test user (run once)
    cursor.execute("INSERT OR IGNORE INTO users (email, password) VALUES (?, ?)", 
                   ("admin", "admin123"))
    conn.commit()
    conn.close()


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # or session.clear()
    return '', 204  # No Content

@app.route('/login', methods=['GET'])
def login_redirect():
    return render_template('login.html')

@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()

    if user:
        session["user"] = username  # Store email in session
        return redirect(url_for("home"))
    else:
        flash("Invalid email or password!")
        return redirect(url_for("index"))


@app.route("/home")
def home():
    if "user" not in session:
        flash("You must log in first.")
        return redirect(url_for("index"))
    return render_template("home.html", user_email=session["user"])

def markdown_to_html(text):
    lines = text.strip().splitlines()
    html_lines = []

    for line in lines:
        match = re.match(r"\*\s*\*\*(.+?):\*\*(.+)", line.strip())
        # print(line.strip())
        if match:
            title, desc = match.groups()
            html_lines.append(f"<li><strong>{title}:</strong>{desc}</li>")
        elif line.strip().startswith("* "):
            html_lines.append(f"<li>{line.strip()[2:]}</li>")
        else:
            html_lines.append(line)
    # print(html_lines)
    return "<ul>" + "\n".join(html_lines) + "</ul>"

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={ACCESS_TOKEN}"

def summarize_text_from_string(content, word_limit=100, bullet=""):
    headers = {
        "Content-Type": "application/json"
    }

    prompt = f"""
        Please Summarize the following text in approximately {word_limit} words. 

        Instruction:
        Please check the content language.
        Please Summarize the content in same language.
        {bullet}.

        Content:
        {content}

        Summary:
    """

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route('/summarize_text', methods=['POST'])
def summarize_text_route():
    data = request.get_json()
    content = data.get("content", "")
    word_limit = int(data.get("word_limit", 100))
    bullet = data.get("bullet", "")

    if not content.strip():
        return jsonify({'result': 'Empty content received.'})

    result = summarize_text_from_string(content, word_limit,bullet)
    result = markdown_to_html(result)
    return jsonify({'result': result})

@app.route('/video_transcript', methods=['POST'])
def video_transcript():
    data = request.get_json()
    video_url = data.get("video_url", "")
    audio_filename = "audio.mp3"
    return jsonify({'result': 'This functionality is not avaiable for demo.'})
    # metadata_json = subprocess.check_output([
    #     "yt-dlp",
    #     "--dump-json",
    #     video_url
    # ], text=True)

    # metadata = json.loads(metadata_json)

    # if (metadata.get("duration") > 120):
    #     return jsonify({'result': "Video duration should be less than 2 mint."}) 

    # # # Step 2: Download audio using yt-dlp
    # subprocess.run([
    #     "yt-dlp",
    #     "-x",
    #     "--audio-format", "mp3",
    #     "-o", audio_filename,
    #     video_url
    # ])

    # # # Step 3: Transcribe using Whisper
    # result = model.transcribe(audio_filename)
    # os.remove(audio_filename)
    # return jsonify({'result': result['text']})

@app.route('/generate_questions_text', methods=['POST'])
def generate_questions_text_route():
    data = request.get_json()
    content = data.get("content", "")
    complexity=data.get("complexity", "simple")

    if not content.strip():
        return jsonify({'result': 'Empty content received.'})

    result = generate_questions_from_string(content, complexity)
    return jsonify({'result': result})

def generate_questions_from_string(content,complexity, num_questions=5):
    
    headers = {
        "Content-Type": "application/json"
    }

    prompt = (
        f"Please Generate {num_questions} multiple choice questions with {complexity} complexity:\n\n"
        f"Content: {content}\n\n"
        f"Format:\n"
        f"1. Question text?\n  a) Option A\n  b) Option B\n  c) Option C\n  d) Option D\nAnswer: <correct option>\n"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
    else:
        return f"Error: {response.status_code} - {response.text}"

if __name__ == '__main__':
    init_db()
    # Dev
    app.run(debug=True, host="0.0.0.0", port=5000)
    # Prod
    # app.run(debug=False, host="0.0.0.0", port=5000)
