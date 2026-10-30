"""
app.py — Flask application factory and entry point.
Run: python app.py
"""

from flask import Flask, render_template, session, redirect, url_for

from config import Config
from utils.db import init_app
from utils.helpers import clock, hhmm

# Blueprint imports
from blueprints.auth       import auth_bp
from blueprints.admin      import admin_bp
from blueprints.member     import member_bp
from blueprints.instructor import instructor_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register DB teardown hook
    init_app(app)

    # Jinja filters for MySQL TIME values (7:00:00 -> 7:00 AM)
    app.add_template_filter(clock, 'clock')
    app.add_template_filter(hhmm, 'hhmm')

    # Register blueprints with URL prefixes
    app.register_blueprint(auth_bp,       url_prefix='/auth')
    app.register_blueprint(admin_bp,      url_prefix='/admin')
    app.register_blueprint(member_bp,     url_prefix='/member')
    app.register_blueprint(instructor_bp, url_prefix='/instructor')

    # ── Root landing page ─────────────────────────────────────
    @app.route('/')
    def index():
        """Public landing page. If already logged in, redirect by role."""
        if 'user_id' in session:
            role = session.get('role')
            if role == 'admin':
                return redirect(url_for('admin.dashboard'))
            if role == 'member':
                return redirect(url_for('member.dashboard'))
            if role == 'instructor':
                return redirect(url_for('instructor.dashboard'))
        return render_template('index.html')

    # ── Custom error pages ────────────────────────────────────
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=5000)
