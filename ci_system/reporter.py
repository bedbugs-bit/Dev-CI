"""
A web reporter built with Flask. It read test result files stored
in TEST_RESULTS_DIR and displays them on a web page. Users can view
the result of CI test in their browser
"""

from flask import Flask, render_template_string, abort
import os
from ci_system import config

app = Flask(__name__)

@app.route("/")
def index():
    # List all commit IDs for which test results exist.
    if os.path.exists(config.TEST_RESULTS_DIR):
        files = os.listdir(config.TEST_RESULTS_DIR)
    else:
        files = []
    html = "<h1>CI Test Results</h1><ul>"
    for file in files:
        html += f'<li><a href="/results/{file}">{file}</a></li>'
    html += "</ul>"
    return html

@app.route("/results/<commit_id>")
def show_result(commit_id):
    file_path = os.path.join(config.TEST_RESULTS_DIR, commit_id)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
        html = f"<h1>Results for Commit {commit_id}</h1><pre>{content}</pre>"
        return html
    else:
        abort(404)

if __name__ == "__main__":
    # Run the Flask app on host 0.0.0.0 to allow external access.
    app.run(host="0.0.0.0", port=5050, debug=True)