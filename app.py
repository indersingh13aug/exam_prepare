from flask import Flask, request, jsonify
import docx
import PyPDF2
import requests
import os
from dotenv import load_dotenv
from flask_cors import CORS

# app = Flask(__name__)

from flask import send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')

CORS(app)
CORS(app, supports_credentials=True)
CORS(app, resources={r"/*": {"origins": "http://localhost:8000"}})
CORS(app, origins=["http://localhost:8000"])

@app.route('/')
def serve_index():
    return send_from_directory('.', 'home.html')



@app.route('/summarize', methods=['POST'])
def summarize():
    file = request.files['file']
    word_limit = int(request.form['word_limit'])
    content_type = request.form['content_type']
    result = summarize_text(file, word_limit, content_type)
    return jsonify({'result': result})

@app.route('/generate_mcq', methods=['POST'])
def generate_mcq_endpoint():
    file = request.files['file']
    complexity = request.form['complexity']
    content_type = request.form['content_type']
    result = generate_mcq(file, complexity, content_type)
    return jsonify({'result': result})


load_dotenv()

ACCESS_TOKEN = os.getenv("GEMINI_API_KEY")

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={ACCESS_TOKEN}"

def summarize_text_from_string(content, word_limit=100, content_type="general"):
    headers = {
        "Content-Type": "application/json"
    }

    prompt = f"""
        You are an expert in summarizing {content_type.lower()} content.
        Summarize the following text in approximately {word_limit} words. Keep the tone and terminology suitable for the {content_type} domain.

        Text:
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
    content_type = data.get("content_type", "general")

    if not content.strip():
        return jsonify({'result': 'Empty content received.'})

    result = summarize_text_from_string(content, word_limit, content_type)
    return jsonify({'result': result})

def read_file(file):
    filepath = file.filename.lower()

    if filepath.endswith('.txt'):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

    elif filepath.endswith('.docx'):
        doc = docx.Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])

    elif filepath.endswith('.pdf'):
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

    else:
        return "Unsupported file format."
    
@app.route('/generate_questions_text', methods=['POST'])
def generate_questions_text_route():
    data = request.get_json()
    content = data.get("content", "")
    content_type = data.get("content_type", "general")
    complexity=data.get("complexity", "simple")

    if not content.strip():
        return jsonify({'result': 'Empty content received.'})

    result = generate_questions_from_string(content, complexity, content_type=content_type)
    return jsonify({'result': result})


def generate_questions_from_string(content,complexity, num_questions=5, content_type="general"):
    print(content)
    headers = {
        "Content-Type": "application/json"
    }

    # prompt = f"""
    #     You are an expert question generator in the field of {content_type.lower()}.
    #     Based on the following content, generate {num_questions} insightful and relevant questions.

    #     Content:
    #     {content}

    #     Questions:
    # """

    prompt = (
        f"The following is a {content_type}. Generate {num_questions} multiple choice questions with {complexity} complexity:\n\n"
        f"{content}\n\n"
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


def generate_mcq(file, complexity, content_type):
    
    content = read_file(file)

    if not content.strip():
        return "File is empty or could not extract content."

    headers = {
        # "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    prompt = (
        f"The following is a {content_type}. Generate 5 multiple choice questions with {complexity} complexity:\n\n"
        f"{content}\n\n"
        f"Format:\n"
        f"1. Question text?\n  a) Option A\n  b) Option B\n  c) Option C\n  d) Option D\nAnswer: <correct option>\n"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
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

def summarize_text(file, word_limit=100, content_type="general"):

    content = read_file(file)
    # print(file)

    if not content.strip():
        return "File is empty or could not extract content."

    headers = {
        # "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    prompt = f"""
        You are an expert in summarizing {content_type.lower()} content.
        Summarize the following text in approximately {word_limit} words. Keep the tone and terminology suitable for the {content_type} domain.

        Text:
        {content}

        Summary:
        """
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
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
    app.run(debug=True)


# if __name__ == '__main__':
#     port = int(os.environ.get("PORT", 5000))
#     app.run(debug=False, host="0.0.0.0", port=port)
