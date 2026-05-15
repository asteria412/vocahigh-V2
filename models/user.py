# =====================================================================
# models/user.py - 회원 테이블 정의
# =====================================================================

import bcrypt
from extensions import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    # -------------------------------------------------------------------
    # 컬럼 정의
    # -------------------------------------------------------------------
    id         = db.Column(db.Integer, primary_key=True)
    nickname   = db.Column(db.String(30), unique=True, nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)

    # 비밀번호는 bcrypt로 해싱된 값만 저장 (원본은 절대 저장 안 함)
    password_hash = db.Column(db.String(255), nullable=False)

    is_admin   = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # -------------------------------------------------------------------
    # 관계 정의
    # -------------------------------------------------------------------
    posts = db.relationship('Post', backref='author', lazy='dynamic')

    # -------------------------------------------------------------------
    # 비밀번호 메서드
    # -------------------------------------------------------------------
    def set_password(self, raw_password):
        """
        평문 비밀번호를 bcrypt로 해싱해서 저장.
        bcrypt는 같은 비밀번호도 매번 다른 해시값을 만들어 (salt 자동 적용).
        rounds=12: 해싱 강도 (높을수록 안전하지만 느림, 12가 일반적 기준)
        """
        hashed = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        # DB에는 문자열로 저장해야 해서 decode
        self.password_hash = hashed.decode('utf-8')

    def check_password(self, raw_password):
        """
        입력한 비밀번호가 저장된 해시와 일치하는지 확인.
        반환값: True(일치) / False(불일치)
        """
        return bcrypt.checkpw(
            raw_password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def __repr__(self):
        return f'<User {self.nickname}>'
