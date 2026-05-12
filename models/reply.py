# =====================================================================
# models/reply.py - 어드민 답변 테이블 정의
# =====================================================================

from extensions import db
from datetime import datetime

class Reply(db.Model):
    __tablename__ = 'replies'

    id = db.Column(db.Integer, primary_key=True)

    # 어떤 게시글에 달린 답변인지
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    # 답변 내용
    content = db.Column(db.Text, nullable=False)

    # 답변 작성 날짜
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Reply to Post {self.post_id}>'
