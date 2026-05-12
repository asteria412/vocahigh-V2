# =====================================================================
# blueprints/board/__init__.py - 학습 상담 게시판 Blueprint 등록
# =====================================================================

from flask import Blueprint

board_bp = Blueprint('board', __name__)

from blueprints.board import routes
