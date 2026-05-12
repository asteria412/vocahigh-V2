# =====================================================================
# models/vocab_list.py - 단어장 테이블
# =====================================================================
# 사용자가 업로드한 PDF/TXT 파일 하나 = VocabList 하나
# =====================================================================

from extensions import db
from datetime import datetime


class VocabList(db.Model):
    __tablename__ = 'vocab_lists'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 단어장 이름 (파일명 또는 사용자가 직접 입력)
    name       = db.Column(db.String(100), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 이 단어장에 속한 단어 목록
    words = db.relationship('VocabWord', backref='vocab_list',
                            lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<VocabList {self.name}>'
