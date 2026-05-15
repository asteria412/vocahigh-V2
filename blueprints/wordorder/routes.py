# =====================================================================
# blueprints/wordorder/routes.py - 어순 배열 연습
# =====================================================================

import re
import random
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from extensions import db
from models.vocab_list import VocabList
from models.vocab_word import VocabWord
from models.score import Score, QUIZ_TYPE_WORDORDER
from core.temp_store import save_temp, load_temp, delete_temp
from services.llm import generate_sentence_puzzle
from blueprints.wordorder import wordorder_bp

MAX_LISTS = 3
MAX_WORDS = 3


# -------------------------------------------------------------------
# 단어장 선택
# -------------------------------------------------------------------
@wordorder_bp.route('/')
@login_required
def setup():
    vocab_lists = VocabList.query.filter_by(user_id=current_user.id)\
                                 .order_by(VocabList.created_at.desc()).all()
    list_info = [{'id': vl.id, 'name': vl.name, 'count': vl.words.count()}
                 for vl in vocab_lists]
    return render_template('wordorder/setup.html', list_info=list_info, max_lists=MAX_LISTS)


# -------------------------------------------------------------------
# 단어 선택 (단어장 선택 후)
# -------------------------------------------------------------------
@wordorder_bp.route('/words', methods=['POST'])
@login_required
def words():
    selected_ids = request.form.getlist('list_ids')

    if not selected_ids:
        flash('단어장을 1개 이상 선택해주세요.', 'danger')
        return redirect(url_for('wordorder.setup'))

    selected_ids = [int(i) for i in selected_ids]
    owned = {vl.id for vl in VocabList.query.filter_by(user_id=current_user.id).all()}
    if not all(i in owned for i in selected_ids):
        flash('잘못된 요청입니다.', 'danger')
        return redirect(url_for('wordorder.setup'))

    # 선택된 단어장의 단어 로드
    all_words = VocabWord.query.filter(
        VocabWord.vocab_list_id.in_(selected_ids)
    ).order_by(VocabWord.zh).all()

    if not all_words:
        flash('선택한 단어장에 단어가 없어요.', 'danger')
        return redirect(url_for('wordorder.setup'))

    # 단어장 이름 맵
    list_names = {vl.id: vl.name for vl in
                  VocabList.query.filter(VocabList.id.in_(selected_ids)).all()}

    word_list = [{
        'id': w.id,
        'zh': w.zh,
        'ko': w.ko,
        'pos': w.pos or '',
        'list_name': list_names.get(w.vocab_list_id, '')
    } for w in all_words]

    return render_template('wordorder/pick.html',
                           word_list=word_list,
                           max_words=MAX_WORDS)


# -------------------------------------------------------------------
# AI 문장 생성
# -------------------------------------------------------------------
@wordorder_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    word_ids_raw = request.form.getlist('word_ids')

    if not word_ids_raw:
        flash('단어를 1개 이상 선택해주세요.', 'danger')
        return redirect(url_for('wordorder.setup'))

    if len(word_ids_raw) > MAX_WORDS:
        flash(f'단어는 최대 {MAX_WORDS}개까지 선택할 수 있어요.', 'danger')
        return redirect(url_for('wordorder.setup'))

    word_ids = [int(i) for i in word_ids_raw]
    words = VocabWord.query.filter(VocabWord.id.in_(word_ids)).all()

    # 소유권 검증
    owned_list_ids = {vl.id for vl in VocabList.query.filter_by(user_id=current_user.id).all()}
    if not all(w.vocab_list_id in owned_list_ids for w in words):
        flash('잘못된 요청입니다.', 'danger')
        return redirect(url_for('wordorder.setup'))

    selected_zh = [w.zh for w in words]

    def _pieces_valid(result):
        """조각을 이어붙인 문장이 전체 문장과 일치하는지 검증 (구두점 제외)"""
        chinese = result.get('chinese', '')
        pieces  = result.get('pieces', [])
        if not pieces or not chinese:
            return False
        joined = ''.join(pieces)
        strip  = lambda s: re.sub(r'[^\w]', '', s, flags=re.UNICODE)
        return strip(joined) == strip(chinese)

    # LLM 호출 — pieces가 전체 문장을 커버할 때까지 최대 3회 재시도
    puzzle = None
    for _ in range(3):
        result = generate_sentence_puzzle(selected_zh)
        if result and _pieces_valid(result):
            puzzle = result
            break

    if not puzzle:
        flash('AI가 문장을 생성하지 못했어요. 다시 시도해주세요.', 'danger')
        return redirect(url_for('wordorder.setup'))

    # pieces 셔플
    pieces = puzzle.get('pieces', [])
    random.shuffle(pieces)
    puzzle['shuffled_pieces'] = pieces

    key = save_temp('wo', puzzle)
    session['wo_key'] = key

    return redirect(url_for('wordorder.play'))


# -------------------------------------------------------------------
# 게임 플레이
# -------------------------------------------------------------------
@wordorder_bp.route('/play')
@login_required
def play():
    key = session.get('wo_key')
    puzzle = load_temp('wo', key)
    if not puzzle:
        flash('문제 데이터가 없어요. 다시 시작해주세요.', 'warning')
        return redirect(url_for('wordorder.setup'))

    return render_template('wordorder/play.html', puzzle=puzzle)


# -------------------------------------------------------------------
# 정답 확인 & 점수 저장
# -------------------------------------------------------------------
@wordorder_bp.route('/check', methods=['POST'])
@login_required
def check():
    key = session.get('wo_key')
    puzzle = load_temp('wo', key)
    if not puzzle:
        flash('문제 데이터가 없어요. 다시 시작해주세요.', 'warning')
        return redirect(url_for('wordorder.setup'))

    user_sentence = request.form.get('user_sentence', '').strip()
    correct_sentence = puzzle.get('chinese', '')

    def normalize(s):
        return re.sub(r'[^\w]', '', s, flags=re.UNICODE)

    is_correct = normalize(user_sentence) == normalize(correct_sentence)

    db.session.add(Score(
        user_id=current_user.id,
        quiz_type=QUIZ_TYPE_WORDORDER,
        score=100.0 if is_correct else 0.0,
        total=100.0
    ))
    db.session.commit()

    # 오답이면 다시 시도 가능하도록 temp 파일 유지
    if is_correct:
        delete_temp('wo', session.pop('wo_key', None))

    return render_template('wordorder/result.html',
                           puzzle=puzzle,
                           user_sentence=user_sentence,
                           is_correct=is_correct)
