# =====================================================================
# blueprints/main/routes.py - 홈 화면 라우트
# =====================================================================

from flask import render_template, send_from_directory, make_response, current_app
from flask_login import current_user
from blueprints.main import main_bp

@main_bp.route('/')
def home():
    return render_template('main/home.html')

@main_bp.route('/sw.js')
def sw():
    response = make_response(send_from_directory(current_app.static_folder, 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Cache-Control'] = 'no-cache'
    return response
