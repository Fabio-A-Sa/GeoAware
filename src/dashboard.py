import os
import json
import threading
import webbrowser
from flask import Flask, render_template_string, jsonify, request
from .reply_templates import get_default_reply
from .scoring import score_message

_TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates', 'dashboard.html')

FOLDERS = ["Earthcaches", "Email", "Message Center"]


def _get_questions(config, gc_code):
    for ec in config.get("earthcaches", []):
        if ec.get("gc") == gc_code:
            return ec.get("questions")
    return None


def _serialize(emails, config):
    emails = sorted(emails, key=lambda e: e.date)
    result = []
    for e in emails:
        questions = _get_questions(config, e.earthcache) if e.earthcache else None
        result.append({
            "id": e.id,
            "geocacher_name": e.geocacher_name or "Unknown",
            "message": e.message_text or "(no message)",
            "gc_code": e.earthcache or "—",
            "date": e.date.strftime("%d/%m/%Y"),
            "default_reply": get_default_reply(
                e.message_text or "",
                name=e.geocacher_name or "",
                gc=e.earthcache or ""
            ),
            "score": score_message(e.message_text, questions),
        })
    return result


def run_dashboard(emails, client, port=5000):
    app = Flask(__name__)
    config = client.config

    with open(_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        _template = f.read()

    emails_by_id = {e.id: e for e in emails}
    initial_data = _serialize(emails, config)

    @app.route("/")
    def index():
        return render_template_string(
            _template,
            initial_emails=json.dumps(initial_data),
            folders=FOLDERS,
            initial_folder="Earthcaches",
        )

    @app.route("/folder/<path:label_name>")
    def folder(label_name):
        try:
            folder_emails = client.get_emails_from_label(label_name, max_results=100)
            emails_by_id.update({e.id: e for e in folder_emails})
            return jsonify(_serialize(folder_emails, config))
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/delete/<email_id>", methods=["POST"])
    def delete(email_id):
        email_obj = emails_by_id.get(email_id)
        if not email_obj:
            return jsonify({"error": "not found"}), 404
        try:
            client.trash_email(email_obj)
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/reply/<email_id>", methods=["POST"])
    def reply(email_id):
        email_obj = emails_by_id.get(email_id)
        if not email_obj:
            return jsonify({"error": "not found"}), 404
        data = request.get_json()
        try:
            client.send_reply(email_obj, data.get("text", ""), send=data.get("send", False))
            return jsonify({"status": "ok"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(port=port, debug=False, use_reloader=False)
