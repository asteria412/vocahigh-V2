# =====================================================================
# blueprints/quiz/routes.py - 주관식 단어 시험
# =====================================================================

import re
import random
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from extensions import db
from models.vocab_list import VocabList
from models.vocab_word import VocabWord
from models.score import Score, QUIZ_TYPE_VOCAB
from core.temp_store import save_temp, load_temp, delete_temp
from blueprints.quiz import quiz_bp

MAX_LISTS = 3


def check_answer(user_input, correct_answer):
    user = str(user_input).strip()
    if not user:
        return False
    candidates = re.split(r'[,/ ]+', str(correct_answer))
    candidates = [c.strip() for c in candidates if c.strip()]
    return user in candidates


# -------------------------------------------------------------------
# 시험 설정 (단어장 선택 + 문제 수)
# -------------------------------------------------------------------
@quiz_bp.route('/')
@login_required
def setup():
    vocab_lists = VocabList.query.filter_by(user_id=current_user.id)\
                                 .order_by(VocabList.created_at.desc()).all()
    list_info = []
    for vl in vocab_lists:
        list_info.append({
            'id': vl.id,
            'name': vl.name,
            'count': vl.words.count()
        })
    return render_template('quiz/setup.html', list_info=list_info, max_lists=MAX_LISTS)


# -------------------------------------------------------------------
# 시험 생성
# -------------------------------------------------------------------
@quiz_bp.route('/start', methods=['POST'])
@login_required
def start():
    selected_ids = request.form.getlist('list_ids')

    if not selected_ids:
        flash('단어장을 1개 이상 선택해주세요.', 'danger')
        return redirect(url_for('quiz.setup'))

    if len(selected_ids) > MAX_LISTS:
        flash(f'단어장은 최대 {MAX_LISTS}개까지 선택할 수 있어요.', 'danger')
        return redirect(url_for('quiz.setup'))

    # 선택된 단어장이 본인 소유인지 검증
    selected_ids = [int(i) for i in selected_ids]
    owned = {vl.id for vl in VocabList.query.filter_by(user_id=current_user.id).all()}
    if not all(i in owned for i in selected_ids):
        flash('잘못된 요청입니다.', 'danger')
        return redirect(url_for('quiz.setup'))

    # 선택된 단어장의 모든 단어 로드
    all_words = VocabWord.query.filter(
        VocabWord.vocab_list_id.in_(selected_ids)
    ).all()

    if not all_words:
        flash('선택한 단어장에 단어가 없어요.', 'danger')
        return redirect(url_for('quiz.setup'))

    try:
        q_count = int(request.form.get('q_count', 10))
    except (ValueError, TypeError):
        q_count = 10

    q_count = max(1, min(q_count, len(all_words)))

    sampled = random.sample(all_words, q_count)
    questions = []
    for word in sampled:
        q_type = random.choice(['zh_to_ko', 'ko_to_zh'])
        questions.append({
            'zh': word.zh,
            'pinyin': word.pinyin or '',
            'ko': word.ko,
            'pos': word.pos or '',
            'type': q_type,
        })

    key = save_temp('quiz', questions)
    session['quiz_key'] = key

    return redirect(url_for('quiz.take'))


# -------------------------------------------------------------------
# 시험 풀기
# -------------------------------------------------------------------
@quiz_bp.route('/take')
@login_required
def take():
    key = session.get('quiz_key')
    questions = load_temp('quiz', key)
    if not questions:
        flash('시험 데이터가 없어요. 다시 시작해주세요.', 'warning')
        return redirect(url_for('quiz.setup'))

    return render_template('quiz/take.html', questions=questions,
                           total=len(questions))


# -------------------------------------------------------------------
# 답안 제출 & 채점
# -------------------------------------------------------------------
@quiz_bp.route('/submit', methods=['POST'])
@login_required
def submit():
    key = session.get('quiz_key')
    questions = load_temp('quiz', key)
    if not questions:
        flash('시험 데이터가 없어요. 다시 시작해주세요.', 'warning')
        return redirect(url_for('quiz.setup'))

    results = []
    correct_count = 0
    excluded_count = 0

    for i, q in enumerate(questions):
        excluded = request.form.get(f'exclude_{i}') == 'on'
        user_ans = request.form.get(f'ans_{i}', '').strip()

        if excluded:
            excluded_count += 1
            results.append({**q, 'user_ans': user_ans, 'excluded': True, 'correct': None})
            continue

        if q['type'] == 'zh_to_ko':
            is_correct = check_answer(user_ans, q['ko'])
        else:
            is_correct = check_answer(user_ans, q['zh'])

        if is_correct:
            correct_count += 1

        results.append({**q, 'user_ans': user_ans, 'excluded': False, 'correct': is_correct})

    final_total = len(questions) - excluded_count
    score_pct = int(correct_count / final_total * 100) if final_total > 0 else 0

    # DB에 점수 저장
    if final_total > 0:
        db.session.add(Score(
            user_id=current_user.id,
            quiz_type=QUIZ_TYPE_VOCAB,
            score=score_pct,
            total=100.0
        ))
        db.session.commit()

    # 임시 파일 정리
    delete_temp('quiz', session.pop('quiz_key', None))

    return render_template('quiz/result.html',
                           results=results,
                           correct=correct_count,
                           final_total=final_total,
                           excluded=excluded_count,
                           score_pct=score_pct)
