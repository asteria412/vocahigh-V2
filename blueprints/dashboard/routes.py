# =====================================================================
# blueprints/dashboard/routes.py - 학습 대시보드
# =====================================================================

import json
from collections import defaultdict
from flask import render_template
from flask_login import login_required, current_user
from models.score import Score
from blueprints.dashboard import dashboard_bp

QUIZ_TYPE_NAMES = {
    'vocab':      '단어시험',
    'wordorder':  '어순연습',
    'writing99':  '작문 99번',
    'writing100': '작문 100번',
}

CHART_COLORS = {
    'vocab':      '#4A90D9',
    'wordorder':  '#F5A623',
    'writing99':  '#28A745',
    'writing100': '#DC3545',
}


@dashboard_bp.route('/')
@login_required
def index():
    scores = Score.query.filter_by(user_id=current_user.id)\
                        .order_by(Score.created_at.asc()).all()

    if not scores:
        return render_template('dashboard/index.html',
                               has_data=False,
                               metrics=None,
                               line_chart=None,
                               bar_chart=None,
                               recent=[])

    # -------------------------------------------------------------------
    # 핵심 지표
    # -------------------------------------------------------------------
    total_count = len(scores)
    avg_score   = round(sum(s.score for s in scores) / total_count, 1)
    last_type   = QUIZ_TYPE_NAMES.get(scores[-1].quiz_type, scores[-1].quiz_type)
    best_score  = max(s.score for s in scores)

    metrics = {
        'total':      total_count,
        'avg':        avg_score,
        'last_type':  last_type,
        'best':       best_score,
    }

    # -------------------------------------------------------------------
    # 꺾은선 차트 — 날짜별 점수 (유형별 색상)
    # -------------------------------------------------------------------
    type_points = defaultdict(list)
    for s in scores:
        type_points[s.quiz_type].append({
            'x': s.created_at.strftime('%m/%d %H:%M'),
            'y': s.score,
        })

    line_datasets = []
    for qtype, points in type_points.items():
        color = CHART_COLORS.get(qtype, '#999')
        line_datasets.append({
            'label':           QUIZ_TYPE_NAMES.get(qtype, qtype),
            'data':            points,
            'borderColor':     color,
            'backgroundColor': color + '33',
            'tension':         0.3,
            'pointRadius':     4,
            'fill':            False,
        })

    line_chart = json.dumps(line_datasets, ensure_ascii=False)

    # -------------------------------------------------------------------
    # 막대 차트 — 유형별 평균 점수
    # -------------------------------------------------------------------
    bar_labels, bar_data, bar_colors = [], [], []
    for qtype, name in QUIZ_TYPE_NAMES.items():
        type_scores = [s.score for s in scores if s.quiz_type == qtype]
        if type_scores:
            bar_labels.append(name)
            bar_data.append(round(sum(type_scores) / len(type_scores), 1))
            bar_colors.append(CHART_COLORS.get(qtype, '#999'))

    bar_chart = json.dumps({
        'labels':  bar_labels,
        'data':    bar_data,
        'colors':  bar_colors,
    }, ensure_ascii=False)

    # -------------------------------------------------------------------
    # 최근 기록 (최신 20개)
    # -------------------------------------------------------------------
    recent = []
    for s in sorted(scores, key=lambda s: s.created_at, reverse=True)[:20]:
        recent.append({
            'date':      s.created_at.strftime('%Y-%m-%d %H:%M'),
            'quiz_type': QUIZ_TYPE_NAMES.get(s.quiz_type, s.quiz_type),
            'score':     int(s.score),
        })

    return render_template('dashboard/index.html',
                           has_data=True,
                           metrics=metrics,
                           line_chart=line_chart,
                           bar_chart=bar_chart,
                           recent=recent)
