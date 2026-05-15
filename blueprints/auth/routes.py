# =====================================================================
# blueprints/auth/routes.py - 회원가입 / 로그인 / 로그아웃
# =====================================================================

from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.user import User
from models.password_reset import PasswordResetRequest
from blueprints.auth import auth_bp
import re


# -------------------------------------------------------------------
# 유효성 검사 함수들
# -------------------------------------------------------------------
def is_valid_email(email):
    """이메일 형식 확인 (간단한 정규식)"""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_register_form(nickname, email, password, password_confirm):
    errors = []

    if not nickname or len(nickname.strip()) < 2:
        errors.append('별명은 2자 이상 입력해주세요.')
    elif len(nickname.strip()) > 30:
        errors.append('별명은 30자 이하로 입력해주세요.')
    elif not re.match(r'^[가-힣a-zA-Z0-9_\-]+$', nickname.strip()):
        errors.append('별명은 한글, 영문, 숫자, _, - 만 사용할 수 있어요.')

    if not email or not is_valid_email(email):
        errors.append('올바른 이메일 주소를 입력해주세요.')
    elif len(email) > 120:
        errors.append('이메일 주소가 너무 길어요.')

    if not password or len(password) < 6:
        errors.append('비밀번호는 6자 이상 입력해주세요.')
    elif len(password) > 100:
        errors.append('비밀번호가 너무 길어요.')

    if password != password_confirm:
        errors.append('비밀번호가 일치하지 않아요.')

    return errors


# -------------------------------------------------------------------
# 회원가입
# -------------------------------------------------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # 이미 로그인된 사용자는 홈으로
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        nickname         = request.form.get('nickname', '').strip()
        email            = request.form.get('email', '').strip().lower()
        password         = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        privacy_agree    = request.form.get('privacy_agree')

        # 1. 개인정보 동의 확인
        if not privacy_agree:
            flash('개인정보 수집에 동의해주세요.', 'danger')
            return render_template('auth/register.html',
                                   form_data={'nickname': nickname, 'email': email})

        # 2. 유효성 검사
        errors = validate_register_form(nickname, email, password, password_confirm)
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html',
                                   form_data={'nickname': nickname, 'email': email})

        # 3. 중복 확인
        if User.query.filter_by(email=email).first():
            flash('이미 사용 중인 이메일이에요.', 'danger')
            return render_template('auth/register.html',
                                   form_data={'nickname': nickname, 'email': email})

        if User.query.filter_by(nickname=nickname).first():
            flash('이미 사용 중인 별명이에요.', 'danger')
            return render_template('auth/register.html',
                                   form_data={'nickname': nickname, 'email': email})

        # 4. 새 유저 생성
        new_user = User(nickname=nickname, email=email)
        new_user.set_password(password)

        # 4. DB에 저장
        db.session.add(new_user)
        db.session.commit()

        flash(f'{nickname}님, 가입을 환영해요! 로그인해주세요.', 'success')
        return redirect(url_for('auth.login'))

    # GET 요청: 빈 폼 보여주기
    return render_template('auth/register.html', form_data={})


# -------------------------------------------------------------------
# 로그인
# -------------------------------------------------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('이메일과 비밀번호를 모두 입력해주세요.', 'danger')
            return render_template('auth/login.html', form_data={'email': email})

        # DB에서 이메일로 유저 찾기
        user = User.query.filter_by(email=email).first()

        # 유저가 없거나 비밀번호가 틀리면 (보안상 같은 메시지로 처리)
        if not user or not user.check_password(password):
            flash('이메일 또는 비밀번호가 올바르지 않아요.', 'danger')
            return render_template('auth/login.html', form_data={'email': email})

        # 로그인 처리 — "로그인 유지" 체크 여부에 따라 쿠키 영속성 결정
        remember_me = bool(request.form.get('remember_me'))
        if not remember_me:
            # permanent=True로 설정해야 PERMANENT_SESSION_LIFETIME(4시간)이 적용됨
            # Chrome 세션복원이 쿠키를 되살려도 4시간 지나면 자동 로그아웃
            session.permanent = True
        login_user(user, remember=remember_me)
        flash(f'어서 와요, {user.nickname}님!', 'success')

        # 로그인 전에 가려던 페이지가 있으면 거기로, 없으면 홈으로
        next_page = request.args.get('next')
        return redirect(next_page or url_for('main.home'))

    return render_template('auth/login.html', form_data={})


# -------------------------------------------------------------------
# 로그아웃
# -------------------------------------------------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('로그아웃됐어요.', 'info')
    return redirect(url_for('main.home'))


# -------------------------------------------------------------------
# 비밀번호 재설정 요청
# -------------------------------------------------------------------
@auth_bp.route('/reset-request', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        email    = request.form.get('email', '').strip().lower()
        pin      = request.form.get('pin', '').strip()

        errors = []
        if not nickname:
            errors.append('별명을 입력해주세요.')
        if not email or not is_valid_email(email):
            errors.append('올바른 이메일 주소를 입력해주세요.')
        if not pin or len(pin) != 4 or not pin.isdigit():
            errors.append('비밀 번호는 숫자 4자리로 입력해주세요.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/reset_request.html',
                                   form_data={'nickname': nickname, 'email': email})

        # 실제 존재하는 계정인지 확인 (보안상 메시지는 동일하게)
        user = User.query.filter_by(nickname=nickname, email=email).first()
        if not user:
            flash('입력하신 정보와 일치하는 계정이 없어요.', 'danger')
            return render_template('auth/reset_request.html',
                                   form_data={'nickname': nickname, 'email': email})

        req = PasswordResetRequest(nickname=nickname, email=email)
        req.set_pin(pin)
        db.session.add(req)
        db.session.commit()

        flash('요청이 접수됐어요. 관리자가 처리하면 이 페이지에서 결과를 확인할 수 있어요.', 'success')
        return redirect(url_for('auth.reset_view'))

    return render_template('auth/reset_request.html', form_data={})


# -------------------------------------------------------------------
# 재설정 결과 확인 (PIN 입력)
# -------------------------------------------------------------------
@auth_bp.route('/reset-view', methods=['GET', 'POST'])
def reset_view():
    reply = None
    status = None

    if request.method == 'POST':
        nickname = request.form.get('nickname', '').strip()
        email    = request.form.get('email', '').strip().lower()
        pin      = request.form.get('pin', '').strip()

        if not all([nickname, email, pin]) or len(pin) != 4 or not pin.isdigit():
            flash('모든 항목을 올바르게 입력해주세요.', 'danger')
            return render_template('auth/reset_view.html')

        req = PasswordResetRequest.query.filter_by(
            nickname=nickname, email=email
        ).order_by(PasswordResetRequest.created_at.desc()).first()

        if not req or not req.check_pin(pin):
            flash('정보가 일치하지 않아요. 별명, 이메일, 비밀 번호를 다시 확인해주세요.', 'danger')
            return render_template('auth/reset_view.html')

        if req.status == 'pending':
            status = 'pending'
        else:
            status = 'done'
            reply = req.admin_reply

    return render_template('auth/reset_view.html', reply=reply, status=status)
