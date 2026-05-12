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

import io
import json
from flask import render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from extensions import db
from models.vocab_list import VocabList
from models.vocab_word import VocabWord
from core.vocab_parser import change_text_to_vocab_df
from blueprints.vocab import vocab_bp

# V1의 PDF 로더 재사용
import fitz  # PyMuPDF


def extract_text_from_file(file):
    """
    업로드된 파일에서 텍스트 추출.
    Flask의 FileStorage 객체를 받아서 문자열로 반환.
    PDF와 TXT 모두 처리.
    """
    filename = file.filename.lower()
    file_bytes = file.read()

    if filename.endswith('.pdf'):
        # PyMuPDF로 PDF 텍스트 추출
        doc = fitz.open(stream=file_bytes, filetype='pdf')
        text = ''
        for page in doc:
            text += page.get_text()
        doc.close()

        # V1과 동일한 손상 감지 로직
        total_chars = len(text)
        readable = sum(1 for c in text if c.isprintable() and not c.isspace())
        if total_chars > 0 and readable / total_chars < 0.8:
            return None  # 손상된 파일

        return text

    elif filename.endswith('.txt'):
        # TXT 파일: UTF-8로 디코딩
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
        text = extract_text_from_file(file)
        if text is None:
            flash('파일을 읽을 수 없어요. 손상된 파일이거나 지원하지 않는 형식이에요.', 'danger')
            return render_template('vocab/upload.html')

        # 단어 파싱 (V1 core/vocab_parser.py 재사용)
        df = change_text_to_vocab_df(text)
        if df is None or df.empty:
            flash('단어를 찾을 수 없어요. 파일 내용을 확인해주세요.', 'danger')
            return render_template('vocab/upload.html')

        # 파싱 결과를 세션에 임시 저장 (검토 화면으로 넘기기 위해)
        words_data = df.to_dict('records')
        session['pending_vocab'] = {
            'list_name': list_name,
            'words': words_data
        }

        flash(f'{len(words_data)}개 단어를 찾았어요. 내용을 확인해주세요.', 'success')
        return redirect(url_for('vocab.review'))

    return render_template('vocab/upload.html')


# -------------------------------------------------------------------
# 파싱 결과 검토 & 저장
# -------------------------------------------------------------------
@vocab_bp.route('/review', methods=['GET', 'POST'])
@login_required
def review():
    # 세션에 대기 중인 단어 데이터가 없으면 업로드 페이지로
    pending = session.get('pending_vocab')
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

        # 세션 정리
        session.pop('pending_vocab', None)

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
