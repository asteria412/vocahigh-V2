# =====================================================================
# create_app.py - Flask 앱 팩토리
# =====================================================================
# "앱 팩토리 패턴": 앱을 함수 안에서 생성하는 방식이야.
# 이렇게 하면 테스트 환경/운영 환경 등 설정을 바꾸기 쉬워.
# =====================================================================

from flask import Flask
from config import config
from extensions import db, login_manager
from models import User, VocabList, VocabWord, Score, PasswordResetRequest  # DB 테이블 생성을 위해 모델 임포트 필요


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
    from blueprints.quiz import quiz_bp
    from blueprints.wordorder import wordorder_bp
    from blueprints.writing import writing_bp
    from blueprints.dictionary import dictionary_bp
    from blueprints.dashboard import dashboard_bp

    # url_prefix: 각 Blueprint의 URL 앞에 붙는 경로
    app.register_blueprint(main_bp)                                    # /
    app.register_blueprint(auth_bp, url_prefix='/auth')                # /auth/
    app.register_blueprint(board_bp, url_prefix='/board')              # /board/
    app.register_blueprint(vocab_bp, url_prefix='/vocab')              # /vocab/
    app.register_blueprint(quiz_bp, url_prefix='/quiz')                # /quiz/
    app.register_blueprint(wordorder_bp, url_prefix='/wordorder')      # /wordorder/
    app.register_blueprint(writing_bp, url_prefix='/writing')          # /writing/
    app.register_blueprint(dictionary_bp, url_prefix='/dictionary')    # /dictionary/
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')      # /dashboard/

    # -------------------------------------------------------------------
    # 뱃지 카운트 context processor (모든 템플릿에서 사용 가능)
    # -------------------------------------------------------------------
    from flask_login import current_user

    @app.context_processor
    def inject_badge_counts():
        if not current_user.is_authenticated:
            return dict(badge_board=0, badge_reset=0, badge_total=0)

        from models.post import Post
        from models.password_reset import PasswordResetRequest

        if current_user.is_admin:
            badge_board = Post.query.filter_by(is_answered=False).count()
            badge_reset = PasswordResetRequest.query.filter_by(status='pending').count()
        else:
            badge_board = Post.query.filter_by(
                user_id=current_user.id,
                is_answered=True,
                reply_viewed=False
            ).count()
            badge_reset = 0

        return dict(
            badge_board=badge_board,
            badge_reset=badge_reset,
            badge_total=badge_board + badge_reset
        )

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
    # DB 테이블 자동 생성 + 임시 파일 청소
    # -------------------------------------------------------------------
    with app.app_context():
        db.create_all()

    from core.temp_store import cleanup_old_temps
    cleanup_old_temps()

    return app
