# =====================================================================
# models/post.py - 게시판 질문 글 테이블 정의
# =====================================================================

from extensions import db
from datetime import datetime

class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)

    # 작성자 ID: users 테이블의 id를 참조하는 외래키
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 글 제목: 최대 200자
    title = db.Column(db.String(200), nullable=False)

    # 글 내용: 길이 제한 없는 텍스트
    content = db.Column(db.Text, nullable=False)

    # 답변 상태: False = 답변 대기, True = 답변 완료
    is_answered = db.Column(db.Boolean, default=False)

    # 유저가 답변을 읽었는지 여부 (False = 새 답변 있음)
    reply_viewed = db.Column(db.Boolean, default=True)

    # 작성 날짜
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 이 게시글에 달린 답변 목록 (Reply 모델과 연결)
    replies = db.relationship('Reply', backref='post', lazy='dynamic')

    def __repr__(self):
        return f'<Post {self.title}>'
