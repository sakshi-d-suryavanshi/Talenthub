import os
import secrets
from flask import Flask, abort, request, session
from werkzeug.security import generate_password_hash

from . import db


def create_app(config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.path.join(app.instance_path, "talenthub.db"),
        COORDINATOR_EMAIL=os.environ.get("COORDINATOR_EMAIL", "coordinator@talenthub.local"),
        COORDINATOR_PASSWORD=os.environ.get("COORDINATOR_PASSWORD", "Admin@1234"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if config:
        app.config.update(config)
    app.config["COORDINATOR_HASH"] = generate_password_hash(app.config["COORDINATOR_PASSWORD"])

    db.init_app(app)
    with app.app_context():
        db.ensure_schema()

    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def csrf_protect():
        if request.method == "POST" and not app.config.get("TESTING"):
            if not secrets.compare_digest(request.form.get("csrf_token", ""), session.get("_csrf", "")):
                abort(400, "Invalid CSRF token")

    @app.context_processor
    def inject_user():
        return {"cur": {"role": session.get("role"), "id": session.get("uid")}}

    from .routes import main, student, company, coordinator
    for bp in (main.bp, student.bp, company.bp, coordinator.bp):
        app.register_blueprint(bp)
    return app
