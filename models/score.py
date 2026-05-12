# =====================================================================
# models/score.py - 학습 점수 기록 테이블
# =====================================================================
# 단어시험/어순/작문 결과를 저장해서 대시보드에 활용
# =====================================================================

from extensions import db
from datetime import datetime


# 학습 유형 상수 (오타 방지용)
QUIZ_TYPE_VOCAB     = 'vocab'      # 단어시험
QUIZ_TYPE_WORDORDER = 'wordorder'  # 어순 배열
QUIZ_TYPE_WRITING99 = 'writing99'  # 작문 99번
QUIZ_TYPE_WRITING100= 'writing100' # 작문 100번


class Score(db.Model):
    __tablename__ = 'scores'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 학습 유형: 'vocab' / 'wordorder' / 'writing99' / 'writing100'
    quiz_type  = db.Column(db.String(20), nullable=False)

    # 점수 (예: 85점 / 100점)
    score      = db.Column(db.Float, nullable=False)
    total      = db.Column(db.Float, default=100.0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Score {self.quiz_type}: {self.score}/{self.total}>'
