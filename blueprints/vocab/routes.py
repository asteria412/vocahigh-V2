# =====================================================================
# blueprints/vocab/routes.py - 단어장 업로드 & 관리
# =====================================================================
# 흐름:
# 1. 사용자가 PDF/TXT 업로드
# 2. core/로 텍스트 추출 + 파싱
# 3. services/llm.py로 AI 보정
# 4. 사용자가 결과 검토 (수정 가능)
# 5. DB에 저장
# =====================================================================

import json
import os
import uuid
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from extensions import db
from models.vocab_list import VocabList
from models.vocab_word import VocabWord
from core.vocab_parser import change_text_to_vocab_df
from blueprints.vocab import vocab_bp

try:
    import pymupdf as fitz
except ImportError:
    import fitz

TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'tmp_vocab')
os.makedirs(TEMP_DIR, exist_ok=True)


def save_pending(words_data, list_name):
    key = str(uuid.uuid4())
    path = os.path.join(TEMP_DIR, f'{key}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'list_name': list_name, 'words': words_data}, f, ensure_ascii=False)
    return key


def load_pending(key):
    if not key:
        return None
    path = os.path.join(TEMP_DIR, f'{key}.json')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def delete_pending(key):
    if not key:
        return
    path = os.path.join(TEMP_DIR, f'{key}.json')
    if os.path.exists(path):
        os.remove(path)


def extract_text_from_file(file):
    """
    업로드된 파일에서 텍스트 추출.
    PDF: text_change.py와 동일한 fitz 로직, Flask용 .read() 적용.
    TXT: UTF-8 / CP949 순으로 디코딩.
    """
    filename = file.filename.lower()

    if filename.endswith('.pdf'):
        pdf_bytes = file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = []
        for page in doc:
            full_text.append(page.get_text())
        doc.close()
        return "\n".join(full_text) or None

    elif filename.endswith('.txt'):
        file_bytes = file.read()
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return file_bytes.decode('cp949', errors='ignore')

    return None


# -------------------------------------------------------------------
# 내 단어장 목록
# -------------------------------------------------------------------
@vocab_bp.route('/')
@login_required
def index():
    # 로그인한 사용자의 단어장 목록 조회 (최신순)
    vocab_lists = VocabList.query.filter_by(user_id=current_user.id)\
                                 .order_by(VocabList.created_at.desc()).all()
    return render_template('vocab/index.html', vocab_lists=vocab_lists)


# -------------------------------------------------------------------
# 단어장 업로드
# -------------------------------------------------------------------
@vocab_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files.get('file')
        list_name = request.form.get('list_name', '').strip()

        # 파일 유무 확인
        if not file or file.filename == '':
            flash('파일을 선택해주세요.', 'danger')
            return render_template('vocab/upload.html')

        # 확장자 확인
        if not (file.filename.lower().endswith('.pdf') or
                file.filename.lower().endswith('.txt')):
            flash('PDF 또는 TXT 파일만 업로드할 수 있어요.', 'danger')
            return render_template('vocab/upload.html')

        # 단어장 이름 기본값: 파일명
        if not list_name:
            list_name = file.filename.rsplit('.', 1)[0]

        # 텍스트 추출
        try:
            text = extract_text_from_file(file)
        except Exception as e:
            flash(f'파일 처리 중 오류: {str(e)}', 'danger')
            return render_template('vocab/upload.html')

        if not text:
            flash('파일에서 텍스트를 추출하지 못했어요. 서버 콘솔 로그를 확인해주세요.', 'danger')
            return render_template('vocab/upload.html')

        # 단어 파싱 (V1 core/vocab_parser.py 재사용)
        df = change_text_to_vocab_df(text)
        if df is None or df.empty:
            flash('단어를 찾을 수 없어요. 파일 내용을 확인해주세요.', 'danger')
            return render_template('vocab/upload.html')

        # 파싱 결과를 임시 파일에 저장 (세션 4KB 한도 우회)
        words_data = df.to_dict('records')
        key = save_pending(words_data, list_name)
        session['pending_key'] = key

        flash(f'{len(words_data)}개 단어를 찾았어요. 내용을 확인해주세요.', 'success')
        return redirect(url_for('vocab.review'))

    return render_template('vocab/upload.html')


# -------------------------------------------------------------------
# 파싱 결과 검토 & 저장
# -------------------------------------------------------------------
@vocab_bp.route('/review', methods=['GET', 'POST'])
@login_required
def review():
    # 임시 파일에서 단어 데이터 로드
    key = session.get('pending_key')
    pending = load_pending(key)
    if not pending:
        return redirect(url_for('vocab.upload'))

    if request.method == 'POST':
        list_name = request.form.get('list_name', pending['list_name']).strip()

        # 폼에서 수정된 단어 데이터 수집
        # 체크박스로 제외한 단어는 포함하지 않음
        selected_indices = request.form.getlist('selected')
        words = pending['words']

        saved_words = []
        for i in selected_indices:
            idx = int(i)
            if idx < len(words):
                word = words[idx]
                # 수정된 값이 있으면 그걸로 교체
                word['zh']     = request.form.get(f'zh_{idx}', word.get('zh', '')).strip()
                word['pinyin'] = request.form.get(f'pinyin_{idx}', word.get('pinyin', '')).strip()
                word['ko']     = request.form.get(f'ko_{idx}', word.get('ko', '')).strip()
                word['pos']    = request.form.get(f'pos_{idx}', word.get('pos', '')).strip()
                if word['zh'] and word['ko']:  # 한자와 의미가 있는 것만 저장
                    saved_words.append(word)

        if not saved_words:
            flash('저장할 단어가 없어요. 최소 1개 이상 선택해주세요.', 'danger')
            return render_template('vocab/review.html',
                                   list_name=pending['list_name'],
                                   words=pending['words'])

        # DB에 저장
        new_list = VocabList(user_id=current_user.id, name=list_name)
        db.session.add(new_list)
        db.session.flush()  # ID 먼저 확보

        for w in saved_words:
            new_word = VocabWord(
                vocab_list_id=new_list.id,
                zh=w.get('zh', ''),
                pinyin=w.get('pinyin', ''),
                ko=w.get('ko', ''),
                pos=w.get('pos', '')
            )
            db.session.add(new_word)

        db.session.commit()

        # 임시 파일 정리
        delete_pending(session.pop('pending_key', None))

        flash(f'"{list_name}" 단어장에 {len(saved_words)}개 단어를 저장했어요!', 'success')
        return redirect(url_for('vocab.index'))

    return render_template('vocab/review.html',
                           list_name=pending['list_name'],
                           words=pending['words'])


# -------------------------------------------------------------------
# 단어장 상세 보기
# -------------------------------------------------------------------
@vocab_bp.route('/<int:list_id>')
@login_required
def detail(list_id):
    vocab_list = VocabList.query.filter_by(
        id=list_id, user_id=current_user.id
    ).first_or_404()

    words = vocab_list.words.all()
    return render_template('vocab/detail.html', vocab_list=vocab_list, words=words)


# -------------------------------------------------------------------
# 단어장 삭제
# -------------------------------------------------------------------
@vocab_bp.route('/<int:list_id>/delete', methods=['POST'])
@login_required
def delete(list_id):
    vocab_list = VocabList.query.filter_by(
        id=list_id, user_id=current_user.id
    ).first_or_404()

    db.session.delete(vocab_list)
    db.session.commit()

    flash(f'"{vocab_list.name}" 단어장을 삭제했어요.', 'info')
    return redirect(url_for('vocab.index'))
