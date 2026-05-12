# =====================================================================
# blueprints/auth/__init__.py - 회원 인증 Blueprint 등록
# =====================================================================

from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from blueprints.auth import routes
