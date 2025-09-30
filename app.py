from flask import Flask, render_template, request, jsonify, send_from_directory
import threading
import os
import shutil
from timetable_logic import run_evolution

app = Flask(__name__, static_folder='.', static_url_path='')

# --- Staff Login Credentials ---
STAFF_CREDENTIALS = {
    'Arpita': '1234',
    'Sanskriti': '1222'
}

# --- Global variables to track state ---
generation_progress = 0
total_generations = 0
best_fitness_so_far = 0.0
is_generating = False
error_message = None

def update_progress_callback(gen, total_gen, fitness, error=None):
    global generation_progress, total_generations, best_fitness_so_far, is_generating, error_message
    generation_progress = gen
    total_generations = total_gen
    best_fitness_so_far = fitness
    if error:
        error_message = error
        is_generating = False

def run_generation_in_background():
    global is_generating, error_message
    is_generating = True
    error_message = None
    run_evolution(update_progress_callback, filename="timetable_preview.html")
    is_generating = False

# --- Main Route - Serves the Single Page Application ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API Endpoints ---
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if username in STAFF_CREDENTIALS and STAFF_CREDENTIALS[username] == password:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "message": "Invalid username or password."})

@app.route('/api/generate', methods=['POST'])
def generate():
    if not is_generating:
        if os.path.exists("timetable_preview.html"):
            os.remove("timetable_preview.html")
        thread = threading.Thread(target=run_generation_in_background)
        thread.start()
    return jsonify({"status": "generation_started"})

@app.route('/api/status')
def status():
    if error_message:
        return jsonify({"status": "error", "message": error_message})
    if is_generating:
        return jsonify({
            "status": "running", "progress": generation_progress,
            "total": total_generations, "fitness": f"{best_fitness_so_far:.4f}"
        })
    elif os.path.exists('timetable_preview.html'):
        return jsonify({"status": "pending_verification"})
    else:
        return jsonify({"status": "idle"})

@app.route('/api/publish', methods=['POST'])
def publish():
    if os.path.exists('timetable_preview.html'):
        shutil.copy('timetable_preview.html', 'timetable.html')
        os.remove('timetable_preview.html')
    return jsonify({"status": "published"})

@app.route('/api/timetable/<timetable_type>')
def get_timetable(timetable_type):
    filename = 'timetable.html' if timetable_type == 'published' else 'timetable_preview.html'
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"found": True, "html": content})
    else:
        return jsonify({"found": False})

if __name__ == '__main__':
    app.run(debug=True)

