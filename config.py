# =====================================================================
# config.py - Flask 앱 설정 파일
# =====================================================================
# 개발환경(Development)과 운영환경(Production)을 분리해서 관리해.
# .env 파일에서 민감한 정보(비밀번호, API 키 등)를 불러와.
# =====================================================================

import os
from datetime import timedelta
from dotenv import load_dotenv

# .env 파일에 있는 환경변수를 불러옴
load_dotenv()

class Config:
    # -------------------------------------------------------------------
    # 보안 설정
    # -------------------------------------------------------------------
    # SECRET_KEY: 세션(로그인 유지) 암호화에 쓰임. 절대 외부에 노출 금지.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'vocahigh-dev-secret-key-change-in-production'

    # -------------------------------------------------------------------
    # 데이터베이스 설정
    # -------------------------------------------------------------------
    # Railway는 mysql:// 형식으로 제공 → pymysql 드라이버용으로 자동 변환
    _db_url = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:1234@localhost/vocahigh'
    if _db_url.startswith('mysql://'):
        _db_url = 'mysql+pymysql://' + _db_url[len('mysql://'):]
    SQLALCHEMY_DATABASE_URI = _db_url

    # SQLAlchemy가 DB 변경사항을 자동으로 추적하는 기능 - 성능에 영향을 줘서 끔
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------------------------------------------
    # 세션 / 쿠키 만료 설정
    # -------------------------------------------------------------------
    # "로그인 유지" 미체크: 4시간 후 자동 로그아웃 (Chrome 세션복원 우회)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)
    # "로그인 유지" 체크: 30일간 쿠키 유지
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    # 요청마다 세션 만료 시간 갱신 (활동 중엔 로그아웃 안 됨)
    SESSION_REFRESH_EACH_REQUEST = True

    # -------------------------------------------------------------------
    # 파일 업로드 설정
    # -------------------------------------------------------------------
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 업로드 최대 파일 크기: 16MB


class DevelopmentConfig(Config):
    # 개발환경: 에러 메시지를 자세히 보여줌
    DEBUG = True


class ProductionConfig(Config):
    # 운영환경: 에러 메시지 숨김 (보안)
    DEBUG = False


# 환경변수 FLASK_ENV 값에 따라 설정을 자동으로 선택
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
