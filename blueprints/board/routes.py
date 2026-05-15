# =====================================================================
# blueprints/board/routes.py - 학습 상담 게시판
# =====================================================================

from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from extensions import db
from models.post import Post
from models.reply import Reply
from models.user import User
from models.password_reset import PasswordResetRequest
from blueprints.auth.decorators import admin_required
from blueprints.board import board_bp

POSTS_PER_PAGE = 10


# -------------------------------------------------------------------
# 게시글 목록
# -------------------------------------------------------------------
@board_bp.route('/')
@login_required
def list():
    page = request.args.get('page', 1, type=int)
    filter_status = request.args.get('status', 'all')  # all / unanswered / answered

    # 관리자는 전체 조회, 일반 유저는 본인 글만
    if current_user.is_admin:
        query = Post.query.order_by(Post.created_at.desc())
    else:
        query = Post.query.filter_by(user_id=current_user.id)\
                          .order_by(Post.created_at.desc())

    if filter_status == 'unanswered':
        query = query.filter_by(is_answered=False)
    elif filter_status == 'answered':
        query = query.filter_by(is_answered=True)

    pagination = query.paginate(page=page, per_page=POSTS_PER_PAGE, error_out=False)

    return render_template('board/list.html',
                           posts=pagination.items,
                           pagination=pagination,
                           filter_status=filter_status)


# -------------------------------------------------------------------
# 글쓰기
# -------------------------------------------------------------------
@board_bp.route('/write', methods=['GET', 'POST'])
@login_required
def write():
    if request.method == 'POST':
        title   = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not title or len(title) < 2:
            flash('제목은 2자 이상 입력해주세요.', 'danger')
            return render_template('board/write.html', form_data={'title': title, 'content': content})

        if not content or len(content) < 5:
            flash('내용은 5자 이상 입력해주세요.', 'danger')
            return render_template('board/write.html', form_data={'title': title, 'content': content})

        post = Post(user_id=current_user.id, title=title, content=content)
        db.session.add(post)
        db.session.commit()

        flash('질문이 등록됐어요!', 'success')
        return redirect(url_for('board.detail', post_id=post.id))

    return render_template('board/write.html', form_data={})


# -------------------------------------------------------------------
# 게시글 상세 + 어드민 답변
# -------------------------------------------------------------------
@board_bp.route('/<int:post_id>', methods=['GET', 'POST'])
@login_required
def detail(post_id):
    post = Post.query.get_or_404(post_id)

    # 본인 글 또는 관리자만 접근 가능
    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    if request.method == 'POST':
        # 어드민만 답변 가능
        if not current_user.is_admin:
            abort(403)

        content = request.form.get('reply_content', '').strip()
        if not content:
            flash('답변 내용을 입력해주세요.', 'danger')
            return redirect(url_for('board.detail', post_id=post_id))

        reply = Reply(post_id=post_id, content=content)
        db.session.add(reply)

        post.is_answered = True
        post.reply_viewed = False
        db.session.commit()

        flash('답변이 등록됐어요.', 'success')
        return redirect(url_for('board.detail', post_id=post_id))

    # 유저가 답변 있는 글을 열면 읽음 처리
    if not current_user.is_admin and post.is_answered and not post.reply_viewed:
        post.reply_viewed = True
        db.session.commit()

    replies = post.replies.order_by(Reply.created_at.asc()).all()
    return render_template('board/detail.html', post=post, replies=replies)


# -------------------------------------------------------------------
# 게시글 삭제
# -------------------------------------------------------------------
@board_bp.route('/<int:post_id>/delete', methods=['POST'])
@login_required
def delete(post_id):
    post = Post.query.get_or_404(post_id)

    if post.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    # 일반 유저는 답변이 달린 글 삭제 불가
    if not current_user.is_admin and post.replies.count() > 0:
        flash('답변 완료된 글은 삭제가 어렵습니다. 관리자에게 문의하세요.', 'danger')
        return redirect(url_for('board.detail', post_id=post_id))

    # 어드민은 답변 포함 전체 삭제 가능
    post.replies.delete()
    db.session.delete(post)
    db.session.commit()

    flash('게시글이 삭제됐어요.', 'info')
    return redirect(url_for('board.list'))


# -------------------------------------------------------------------
# 비밀번호 재설정 요청 목록 (어드민 전용)
# -------------------------------------------------------------------
@board_bp.route('/reset-requests')
@login_required
@admin_required
def reset_requests():
    requests = PasswordResetRequest.query\
                   .order_by(PasswordResetRequest.created_at.desc()).all()
    return render_template('board/reset_requests.html', requests=requests)


# -------------------------------------------------------------------
# 비밀번호 재설정 처리 (어드민 전용)
# -------------------------------------------------------------------
@board_bp.route('/reset-requests/<int:req_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_reset_request(req_id):
    req = PasswordResetRequest.query.get_or_404(req_id)

    temp_pw    = request.form.get('temp_password', '').strip()
    admin_note = request.form.get('admin_note', '').strip()

    if not temp_pw or len(temp_pw) < 6:
        flash('임시 비밀번호는 6자 이상이어야 해요.', 'danger')
        return redirect(url_for('board.reset_requests'))

    user = User.query.filter_by(nickname=req.nickname, email=req.email).first()
    if not user:
        flash('해당 계정을 찾을 수 없어요.', 'danger')
        return redirect(url_for('board.reset_requests'))

    user.set_password(temp_pw)
    user.force_password_reset = True

    reply_text = f'임시 비밀번호: {temp_pw}'
    if admin_note:
        reply_text += f'\n\n{admin_note}'

    req.admin_reply = reply_text
    req.status = 'done'
    db.session.commit()

    flash(f'{req.nickname}님의 비밀번호가 초기화됐어요.', 'success')
    return redirect(url_for('board.reset_requests'))


# -------------------------------------------------------------------
# 답변 삭제 (어드민 전용)
# -------------------------------------------------------------------
@board_bp.route('/<int:post_id>/reply/<int:reply_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_reply(post_id, reply_id):
    reply = Reply.query.get_or_404(reply_id)
    post  = Post.query.get_or_404(post_id)

    db.session.delete(reply)

    # 남은 답변이 없으면 미답변 상태로 되돌림
    if post.replies.count() == 0:
        post.is_answered = False

    db.session.commit()

    flash('답변이 삭제됐어요.', 'info')
    return redirect(url_for('board.detail', post_id=post_id))
