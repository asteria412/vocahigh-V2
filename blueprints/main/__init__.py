# =====================================================================
# blueprints/main/__init__.py - 메인(홈) Blueprint 등록
# =====================================================================
# Blueprint: Flask에서 기능을 모듈별로 나누는 방법이야.
# 'main'이라는 이름의 Blueprint를 만들어서 홈 화면 관련 라우트를 여기에 모아.
# =====================================================================

from flask import Blueprint

# Blueprint 객체 생성
# 첫 번째 인자: Blueprint 이름 (URL 생성 시 'main.함수명' 형식으로 사용)
# __name__: 현재 파일의 위치를 Flask에게 알려줌
main_bp = Blueprint('main', __name__)

# 라우트 파일을 여기서 임포트 (Blueprint 등록 후 불러와야 순환 참조 없음)
from blueprints.main import routes
