# =====================================================================
# create_app.py - Flask 앱 팩토리
# =====================================================================
# "앱 팩토리 패턴": 앱을 함수 안에서 생성하는 방식이야.
# 이렇게 하면 테스트 환경/운영 환경 등 설정을 바꾸기 쉬워.
# =====================================================================

from flask import Flask
from config import config
from extensions import db, login_manager
from models import User, VocabList, VocabWord, Score  # DB 테이블 생성을 위해 모델 임포트 필요


def create_app(config_name='default'):
    # Flask 앱 객체 생성
    app = Flask(__name__)

    # config.py에서 설정 불러오기
    app.config.from_object(config[config_name])

    # -------------------------------------------------------------------
    # 확장 모듈을 앱에 연결
    # -------------------------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)

    # -------------------------------------------------------------------
    # Flask-Login: 세션에서 유저 정보를 불러오는 함수 등록
    # -------------------------------------------------------------------
    # 로그인된 사용자의 ID를 받아서 DB에서 User 객체를 찾아 반환
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # -------------------------------------------------------------------
    # Blueprint 등록
    # -------------------------------------------------------------------
    from blueprints.main import main_bp
    from blueprints.auth import auth_bp
    from blueprints.board import board_bp
    from blueprints.vocab import vocab_bp

    # url_prefix: 각 Blueprint의 URL 앞에 붙는 경로
    app.register_blueprint(main_bp)                        # /
    app.register_blueprint(auth_bp, url_prefix='/auth')    # /auth/login, /auth/register
    app.register_blueprint(board_bp, url_prefix='/board')  # /board/
    app.register_blueprint(vocab_bp, url_prefix='/vocab')  # /vocab/

    # -------------------------------------------------------------------
    # 에러 핸들러 등록
    # -------------------------------------------------------------------
    from flask import render_template

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    # -------------------------------------------------------------------
    # DB 테이블 자동 생성
    # -------------------------------------------------------------------
    with app.app_context():
        db.create_all()

    return app
