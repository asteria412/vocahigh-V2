# =====================================================================
# config.py - Flask 앱 설정 파일
# =====================================================================
# 개발환경(Development)과 운영환경(Production)을 분리해서 관리해.
# .env 파일에서 민감한 정보(비밀번호, API 키 등)를 불러와.
# =====================================================================

import os
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
    # MySQL 연결 주소 형식: mysql+pymysql://유저명:비밀번호@호스트/DB이름
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:1234@localhost/vocahigh'

    # SQLAlchemy가 DB 변경사항을 자동으로 추적하는 기능 - 성능에 영향을 줘서 끔
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
