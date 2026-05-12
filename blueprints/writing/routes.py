# =====================================================================
# blueprints/writing/routes.py - HSK 작문 연습 (99번 / 100번)
# =====================================================================

import json
import os
import uuid
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from extensions import db
from models.vocab_list import VocabList
from models.vocab_word import VocabWord
from models.score import Score, QUIZ_TYPE_WRITING99, QUIZ_TYPE_WRITING100
from services.llm import (
    generate_hybrid_question_99,
    generate_scene_description,
    generate_image_from_text,
    evaluate_writing_v2,
)
from blueprints.writing import writing_bp

TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'tmp_vocab')
os.makedirs(TEMP_DIR, exist_ok=True)

MAX_LISTS = 3


def _save(prefix, data):
    key = str(uuid.uuid4())
    path = os.path.join(TEMP_DIR, f'{prefix}_{key}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    return key


def _load(prefix, key):
    if not key:
        return None
    path = os.path.join(TEMP_DIR, f'{prefix}_{key}.json')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _delete(prefix, key):
    if not key:
        return
    path = os.path.join(TEMP_DIR, f'{prefix}_{key}.json')
    if os.path.exists(path):
        os.remove(path)


# -------------------------------------------------------------------
# 진입점
# -------------------------------------------------------------------
@writing_bp.route('/')
@login_required
def index():
    return redirect(url_for('writing.setup_99'))


# ===================================================================
# 99번 — 제시어 작문
# ===================================================================

@writing_bp.route('/99')
@login_required
def setup_99():
    vocab_lists = VocabList.query.filter_by(user_id=current_user.id)\
                                 .order_by(VocabList.created_at.desc()).all()
    list_info = [{'id': vl.id, 'name': vl.name, 'count': vl.words.count()}
                 for vl in vocab_lists]
    return render_template('writing/setup_99.html',
                           list_info=list_info, max_lists=MAX_LISTS)


@writing_bp.route('/99/gen', methods=['POST'])
@login_required
def gen_99():
    selected_ids = request.form.getlist('list_ids')

    if not selected_ids:
        flash('단어장을 1개 이상 선택해주세요.', 'danger')
        return redirect(url_for('writing.setup_99'))

    selected_ids = [int(i) for i in selected_ids]
    owned = {vl.id for vl in VocabList.query.filter_by(user_id=current_user.id).all()}
    if not all(i in owned for i in selected_ids):
        flash('잘못된 요청입니다.', 'danger')
        return redirect(url_for('writing.setup_99'))

    all_words = VocabWord.query.filter(
        VocabWord.vocab_list_id.in_(selected_ids)
    ).all()

    if len(all_words) < 3:
        flash('단어가 최소 3개 이상 있어야 문제를 생성할 수 있어요.', 'danger')
        return redirect(url_for('writing.setup_99'))

    word_dicts = [w.to_dict() for w in all_words]
    hybrid = generate_hybrid_question_99(word_dicts)

    if not hybrid:
        flash('AI 문제 생성에 실패했어요. 잠시 후 다시 시도해주세요.', 'danger')
        return redirect(url_for('writing.setup_99'))

    # 채점용 한자 리스트 추출
    target_zh_list = [w['zh'] for w in hybrid['words']]
    data = {
        'theme': hybrid.get('theme', ''),
        'words': hybrid['words'],
        'target_zh_list': target_zh_list,
    }

    key = _save('wr99', data)
    session['wr99_key'] = key
    return redirect(url_for('writing.write_99'))


@writing_bp.route('/99/write')
@login_required
def write_99():
    key = session.get('wr99_key')
    data = _load('wr99', key)
    if not data:
        flash('문제가 없어요. 다시 생성해주세요.', 'warning')
        return redirect(url_for('writing.setup_99'))
    return render_template('writing/write_99.html', data=data)


@writing_bp.route('/99/eval', methods=['POST'])
@login_required
def eval_99():
    key = session.get('wr99_key')
    data = _load('wr99', key)
    if not data:
        flash('문제 데이터가 없어요.', 'warning')
        return redirect(url_for('writing.setup_99'))

    user_input = request.form.get('user_input', '').strip()
    if not user_input:
        flash('답안을 입력해주세요.', 'danger')
        return redirect(url_for('writing.write_99'))

    feedback = evaluate_writing_v2('99', user_input, data['target_zh_list'])
    if not feedback:
        flash('채점 중 오류가 발생했어요. 다시 시도해주세요.', 'danger')
        return redirect(url_for('writing.write_99'))

    db.session.add(Score(
        user_id=current_user.id,
        quiz_type=QUIZ_TYPE_WRITING99,
        score=feedback['score'],
        total=100.0
    ))
    db.session.commit()
    _delete('wr99', session.pop('wr99_key', None))

    return render_template('writing/result_99.html',
                           data=data,
                           user_input=user_input,
                           feedback=feedback)


# ===================================================================
# 100번 — 그림 작문
# ===================================================================

@writing_bp.route('/100')
@login_required
def setup_100():
    return render_template('writing/setup_100.html')


@writing_bp.route('/100/gen', methods=['POST'])
@login_required
def gen_100():
    scene = generate_scene_description()
    if not scene:
        flash('문제 생성에 실패했어요. 잠시 후 다시 시도해주세요.', 'danger')
        return redirect(url_for('writing.setup_100'))

    # DALL-E 이미지 생성 (실패해도 텍스트로 대체)
    image_url = generate_image_from_text(scene['scene_desc'])

    data = {
        'scene_desc': scene['scene_desc'],
        'keywords': scene.get('keywords', []),
        'image_url': image_url,
    }

    key = _save('wr100', data)
    session['wr100_key'] = key
    return redirect(url_for('writing.write_100'))


@writing_bp.route('/100/write')
@login_required
def write_100():
    key = session.get('wr100_key')
    data = _load('wr100', key)
    if not data:
        flash('문제가 없어요. 다시 생성해주세요.', 'warning')
        return redirect(url_for('writing.setup_100'))
    return render_template('writing/write_100.html', data=data)


@writing_bp.route('/100/eval', methods=['POST'])
@login_required
def eval_100():
    key = session.get('wr100_key')
    data = _load('wr100', key)
    if not data:
        flash('문제 데이터가 없어요.', 'warning')
        return redirect(url_for('writing.setup_100'))

    user_input = request.form.get('user_input', '').strip()
    if not user_input:
        flash('답안을 입력해주세요.', 'danger')
        return redirect(url_for('writing.write_100'))

    feedback = evaluate_writing_v2('100', user_input, data['scene_desc'])
    if not feedback:
        flash('채점 중 오류가 발생했어요. 다시 시도해주세요.', 'danger')
        return redirect(url_for('writing.write_100'))

    db.session.add(Score(
        user_id=current_user.id,
        quiz_type=QUIZ_TYPE_WRITING100,
        score=feedback['score'],
        total=100.0
    ))
    db.session.commit()
    _delete('wr100', session.pop('wr100_key', None))

    return render_template('writing/result_100.html',
                           data=data,
                           user_input=user_input,
                           feedback=feedback)
