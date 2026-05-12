# =====================================================================
# blueprints/auth/decorators.py - 커스텀 데코레이터
# =====================================================================
# 데코레이터: 함수 위에 @붙여서 쓰는 것.
# @login_required 처럼 어드민 전용 페이지를 보호할 때 사용해.
# =====================================================================

from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    """
    어드민 전용 라우트 보호 데코레이터.
    사용법: 라우트 함수 위에 @admin_required 붙이면 됨.
    비로그인 또는 일반 유저가 접근하면 403 에러 반환.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 로그인 안 됐거나 어드민이 아니면 403 Forbidden
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
