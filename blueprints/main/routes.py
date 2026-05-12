# =====================================================================
# blueprints/main/routes.py - 홈 화면 라우트
# =====================================================================

from flask import render_template
from flask_login import current_user
from blueprints.main import main_bp

@main_bp.route('/')
def home():
    # 홈 화면: 로그인 여부에 따라 다른 내용을 보여줄 수 있어
    return render_template('main/home.html')
