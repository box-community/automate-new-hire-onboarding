from dotenv import load_dotenv
from flask import Flask, request, jsonify

from onboarding import onboard_new_hire

load_dotenv()
app = Flask(__name__)


@app.route("/")
def index():
    """Friendly landing page with usage hints."""
    return jsonify(
        {
            "service": "Box new hire onboarding workspaces",
            "endpoints": {
                "POST /hire": (
                    "Receive an employee.hired event and provision a "
                    "standardized, governed Box workspace"
                ),
                "GET /health": "Liveness check",
            },
            "local_test": (
                "curl -X POST http://127.0.0.1:5000/hire "
                '-H "Content-Type: application/json" '
                "-d @sample_hire_event.json"
            ),
        }
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/hire", methods=["POST"])
def handle_hire_event():
    """Handle HR hired events and provision a workspace.

    In production, verify that requests originate from your HR system
    (signature or shared secret) before provisioning anything.
    """
    event = request.get_json()

    if not event or event.get("event") != "employee.hired":
        return jsonify({"status": "ignored"}), 200

    employee = event["employee"]
    hire = {
        "name": employee["full_name"],
        "email": employee.get("work_email"),
    }

    workspace_id = onboard_new_hire(hire)

    return jsonify({"status": "provisioned", "workspace_id": workspace_id}), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
