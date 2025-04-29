from flask import Flask, render_template, request, jsonify
import os
import requests
from docx import Document
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

MODEL_API_URL = 'http://193:1234/v1/completions'  # Change this to your model API URL

def get_text_from_docx(filepath):
    doc = Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])

def get_model_score(user_input, doc_text):
    prompt = (
        f"Given the following document content:\n\n{doc_text}\n\n"
        f"How well does it match the query: '{user_input}'?\n"
        "Respond with a match score between 0 to 100."
    )
    payload = {
        "model": "gemma-2-2b-it",
        "prompt": prompt,
        "max_tokens": 150
    }
    try:
        res = requests.post(MODEL_API_URL, json=payload)
        if res.status_code == 200:
            text = res.json()['choices'][0]['text']
            score = int(''.join(filter(str.isdigit, text)))
            return min(max(score, 0), 100)
        return 0
    except:
        return 0

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    user_input = request.form['user_input']
    files = request.files.getlist('files')
    results = []

    for file in files:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        doc_text = get_text_from_docx(filepath)
        score = get_model_score(user_input, doc_text)

        results.append({
            "filename": filename,
            "score": score
        })

    sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
    return jsonify(sorted_results)

if __name__ == '__main__':
    app.run(debug=True)
