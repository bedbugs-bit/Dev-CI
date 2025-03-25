"""
A web reporter built with Flask. It read test result files stored
in TEST_RESULTS_DIR and displays them on a web page. Users can view
the result of CI test in their browser
"""

from flask import Flask, render_template_string, abort
from pathlib import Path
import os
from ci_system import config

app = Flask(__name__)
app.config['TEST_RESULTS_DIR'] = config.TEST_RESULTS_DIR

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CI Test Results</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .commit-list { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .test-results { background: white; padding: 25px; border-radius: 8px; margin-top: 20px; }
        pre { 
            padding: 15px; 
            background: #f8f9fa; 
            border: 1px solid #eee; 
            border-radius: 4px; 
            white-space: pre-wrap; 
            word-wrap: break-word;
        }
        a { text-decoration: none; }
        .badge { font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">🛠️ CI Test Results</h1>
        <div class="commit-list">
            {% if commits %}
                <div class="list-group">
                    {% for commit in commits %}
                    <a href="/results/{{ commit.id }}" class="list-group-item list-group-item-action d-flex justify-content-between align-items-center">
                        <span>
                            <span class="badge bg-primary me-2">{{ commit.status }}</span>
                            {{ commit.id }}
                        </span>
                        <small class="text-muted">{{ commit.date }}</small>
                    </a>
                    {% endfor %}
                </div>
            {% else %}
                <div class="alert alert-info">No test results available yet</div>
            {% endif %}
        </div>
        
        {% if result %}
        <div class="test-results mt-4">
            <h3>Results for {{ result.commit_id }}</h3>
            <div class="alert alert-{{ 'success' if result.passed else 'danger' }}">
                Test suite {{ "passed" if result.passed else "failed" }}
            </div>
            <pre><code>{{ result.content }}</code></pre>
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

def get_commit_info(commit_id):
    """Extract test result metadata"""
    file_path = config.TEST_RESULTS_DIR / commit_id
    if not file_path.exists():
        return None
        
    with open(file_path, 'r') as f:
        content = f.read()
        
    return {
        'id': commit_id,
        'status': 'passed' if 'OK' in content else 'failed',
        'date': os.path.getctime(file_path),
        'content': content
    }

@app.route("/")
def index():
    commits = []
    if config.TEST_RESULTS_DIR.exists():
        for f in config.TEST_RESULTS_DIR.iterdir():
            if f.is_file():
                commit = get_commit_info(f.name)
                if commit:
                    commits.append(commit)
    
    # Sort by creation date descending
    commits.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template_string(HTML_TEMPLATE, commits=commits)

@app.route("/results/<commit_id>")
def show_result(commit_id):
    commit = get_commit_info(commit_id)
    if not commit:
        abort(404)
        
    return render_template_string(
        HTML_TEMPLATE,
        commits=[commit],  # Show single result in list
        result={
            'commit_id': commit_id,
            'content': commit['content'],
            'passed': commit['status'] == 'passed'
        }
    )

@app.errorhandler(404)
def page_not_found(e):
    return render_template_string("""
        <div class="container mt-5">
            <div class="alert alert-danger">
                <h4>Commit not found</h4>
                <p>The requested test results could not be found</p>
            </div>
        </div>
    """), 404

if __name__ == "__main__":
    app.run(
        host=config.REPORTER_HOST,
        port=config.REPORTER_PORT,
        debug=(config.LOG_LEVEL == "DEBUG")
    )