from flask import Flask, render_template, send_from_directory
import os

# All the AI logic has been moved to JavaScript.
# This server's only job is to serve the files.
app = Flask(__name__, static_folder='static', static_url_path='/static')

@app.route('/')
def home():
    """Serves the main single-page application."""
    return render_template('index.html')

@app.route('/data/<filename>')
def get_data(filename):
    """Provides the CSV data files to the frontend."""
    return send_from_directory('.', filename)

if __name__ == '__main__':
    app.run(debug=True)

