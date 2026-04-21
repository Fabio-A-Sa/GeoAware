import os
import threading
import webbrowser
from flask import Flask, render_template_string, jsonify

_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates', 'dashboard.html')

def run_dashboard(emails, port=5000):
    app = Flask(__name__)

    with open(_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        _template = f.read()

    email_data = [
        {
            "id": e.id,
            "geocacher_name": e.geocacher_name or "Unknown",
            "message": e.message_text or "(no message)",
            "gc_code": e.earthcache or "—",
        }
        for e in emails
    ]

    @app.route("/")
    def index():
        return render_template_string(_template, emails=email_data)

    @app.route("/reply/<email_id>", methods=["POST"])
    def reply(email_id):
        return jsonify({"status": "ok"})

    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(port=port, debug=False, use_reloader=False)
