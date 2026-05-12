# =====================================================================
# blueprints/board/routes.py - 게시판 라우트
# =====================================================================
# Day 15~17에 실제 로직을 채울 거야. 지금은 뼈대만.
# =====================================================================

from flask import render_template
from flask_login import login_required
from blueprints.board import board_bp

@board_bp.route('/')
def list():
    # 게시글 목록 (Day 15에 구현 예정)
    return render_template('board/list.html')

@board_bp.route('/<int:post_id>')
def detail(post_id):
    # 게시글 상세보기 (Day 15에 구현 예정)
    return render_template('board/detail.html', post_id=post_id)
