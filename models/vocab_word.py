# =====================================================================
# models/vocab_word.py - 단어 테이블
# =====================================================================
# 단어장(VocabList) 하나에 여러 단어(VocabWord)가 속함
# =====================================================================

from extensions import db


class VocabWord(db.Model):
    __tablename__ = 'vocab_words'

    id            = db.Column(db.Integer, primary_key=True)
    vocab_list_id = db.Column(db.Integer, db.ForeignKey('vocab_lists.id'), nullable=False)

    zh      = db.Column(db.String(50),  nullable=False)   # 한자 (예: 学习)
    pinyin  = db.Column(db.String(200))                  # 병음 (예: xuéxí)
    ko      = db.Column(db.String(500), nullable=False)  # 한국어 의미 (예: 학습하다)
    pos     = db.Column(db.String(20))                   # 품사 (예: 동사, 명사)

    def to_dict(self):
        # 단어 정보를 딕셔너리로 반환 (JSON 변환, 세션 저장에 사용)
        return {
            'id': self.id,
            'zh': self.zh,
            'pinyin': self.pinyin,
            'ko': self.ko,
            'pos': self.pos
        }

    def __repr__(self):
        return f'<VocabWord {self.zh}>'
