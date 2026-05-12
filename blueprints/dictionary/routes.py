# =====================================================================
# blueprints/dictionary/routes.py - AI 단어 사전
# =====================================================================

from flask import render_template, request
from flask_login import login_required, current_user
from extensions import db
from models.vocab_list import VocabList
from models.vocab_word import VocabWord
from services.llm import search_word_info
from blueprints.dictionary import dictionary_bp


def _local_search(keyword, user_id):
    """내 모든 단어장에서 부분 일치 검색 (한자 or 한국어 뜻)"""
    return VocabWord.query\
        .join(VocabList, VocabWord.vocab_list_id == VocabList.id)\
        .filter(
            VocabList.user_id == user_id,
            db.or_(
                VocabWord.zh.contains(keyword),
                VocabWord.ko.contains(keyword)
            )
        ).all()


# -------------------------------------------------------------------
# 검색 페이지 (로컬 결과)
# -------------------------------------------------------------------
@dictionary_bp.route('/')
@login_required
def index():
    keyword = request.args.get('q', '').strip()
    local_results = []

    if keyword:
        local_results = _local_search(keyword, current_user.id)

    return render_template('dictionary/index.html',
                           keyword=keyword,
                           local_results=local_results,
                           ai_result=None)


# -------------------------------------------------------------------
# AI 상세 검색
# -------------------------------------------------------------------
@dictionary_bp.route('/ai', methods=['POST'])
@login_required
def ai_search():
    keyword = request.form.get('keyword', '').strip()
    local_results = []
    ai_result = None
    ai_error = False

    if keyword:
        local_results = _local_search(keyword, current_user.id)
        ai_result = search_word_info(keyword)
        if not ai_result:
            ai_error = True

    return render_template('dictionary/index.html',
                           keyword=keyword,
                           local_results=local_results,
                           ai_result=ai_result,
                           ai_error=ai_error)
