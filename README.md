# 🌊 voca海 (voca High) — V2

<div align="center">

> **"단어의 바다를 건너, 이제는 앱으로 날다."**
>
> HSK 수험생을 위한 AI 맞춤 학습 플랫폼 — 이제 진짜 앱이 됐습니다.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-Railway-orange?logo=mysql)](https://railway.app)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green?logo=openai)](https://openai.com)
[![PWA](https://img.shields.io/badge/PWA-설치가능-purple?logo=pwa)](https://web.dev/pwa)

</div>

---

## 🕰️ V1의 추억: 우리가 여기까지 온 이야기

V1은 용감했습니다.
Streamlit 하나로 AI 단어 시험, 어순 연습, 작문까지 — 거의 맨손으로 만든 학습 도구였습니다.
데이터는 Google Sheets에, UI는 Streamlit 기본 테마에, 
인증은 '별명 하나'로. 그것으로도 충분히 쓸만했지만, **저는 더 원했습니다.**

> _"내 폰 홈 화면에 깔고 싶다."_
> _"로그인하고 내 기록이 쌓였으면 좋겠다."_
> _"더 앱처럼 생겼으면 좋겠다."_

**그래서 V2가 태어났습니다.**

---

## ⚡ V1 vs V2 — 무엇이 달라졌나?

| 항목 | V1 (Streamlit) | V2 (Flask) | 한 줄 요약 |
|:---|:---:|:---:|:---|
| **프레임워크** | Streamlit | Flask + Blueprint | 진짜 웹 앱 구조로 |
| **데이터베이스** | Google Sheets | MySQL (Railway) | 엑셀 탈출, 진짜 DB |
| **사용자 인증** | 별명만 입력 | bcrypt + Flask-Login | 내 계정, 내 기록 |
| **배포 환경** | 로컬 실행 | Railway 클라우드 | 언제 어디서나 접속 |
| **모바일 지원** | 제한적 | 반응형 + PWA | 폰에 설치까지 가능 |
| **네비게이션** | Streamlit 사이드바 | 상단바 + 하단 탭바 | 앱처럼 자연스럽게 |
| **이미지 생성** | DALL-E 3 | gpt-image-1.5 | 최신 모델로 업그레이드 |
| **학습 게시판** | ❌ | ✅ | 선생님께 질문 가능 |
| **대시보드** | Google Sheets 링크 | 실시간 학습 통계 | 내 성장을 한눈에 |
| **UI/UX** | Streamlit 기본 | 커스텀 CSS 디자인 | 이제 진짜 예쁨 |

---

## 🚀 V2 핵심 기능

### 📚 단어장 — 내 것만 공부한다
PDF·TXT 파일을 업로드하면 AI가 단어·병음·뜻을 자동 추출합니다.
내가 공부하는 단어장에서만 문제가 나옵니다. 불필요한 건 없어요.

### 🧪 단어 시험 — 깐깐하게, 정확하게
원본 텍스트를 AI가 직접 참조하여 병음·뜻을 복원하고 문제를 출제합니다.
4지선다 → 정답 확인 → 오답 복습까지 한 흐름으로.

### 🔀 어순 연습 — HSK 전략이 녹아든 문제
단순 셔플이 아닙니다.
**호응 관계 · 복잡 수식 구조 · 논리 접속사** — HSK 3대 핵심 출제 패턴을 기반으로
AI가 직접 문장을 골라 섞습니다.

### ✍️ 작문 연습 — 99번 & 100번 완전 재현
- **99번 제시어**: 내 단어 3개 + AI 트렌드 단어 2개의 하이브리드 작문 출제
- **100번 그림**: gpt-image-1.5가 4대 빈출 테마(비즈니스/일상/스포츠/학습)로 랜덤 상황화 → 이미지 생성
- AI 채점: **냉정한 가점제** — 기본점 + 고급 어휘/문형에만 가산점

### 🔍 사전 — 외부 앱 필요 없음
앱 안에서 바로 검색. 병음·뜻·예문까지.

### 📊 대시보드 — 내 성장 기록
영역별 시험 점수, 학습 횟수, 추이 그래프 — 나의 학습이 데이터로 쌓입니다.

### 💬 학습 상담 게시판 — 혼자 아닌 함께
모르는 게 생겼을 때 질문을 남기면 답변이 달립니다.
답변 대기 / 답변 완료 필터로 깔끔하게 관리.

### 🔐 계정 관리 — 안전하게, 간편하게
- **회원가입**: 별명 · 이메일 중복 확인 + 입력값 검증
- **비밀번호 변경**: 로그인 상태에서 현재 비밀번호 확인 후 변경
- **비밀번호 재설정 요청**: 비밀번호를 잊은 경우 별명 · 이메일 · 4자리 비밀 번호로 요청 → 관리자가 임시 비밀번호 설정 → 비밀 번호 입력으로 결과 확인

### 🔔 알림 — 놓치지 않는 피드백
- **관리자**: 미답변 학습 상담 · 미처리 비밀번호 재설정 요청 발생 시 뱃지 알림으로 신속 대응
- **유저**: 학습 상담 답변이 달리면 앱 아이콘 및 메뉴에 뱃지 알림

---

## 📱 PWA — 진짜 앱처럼 설치하세요

V2는 **Progressive Web App**입니다.
Safari(iOS) 또는 Chrome(Android)에서 **"홈 화면에 추가"** 하면:

- 홈 화면에 전용 아이콘 생성
- 상단 주소창 없이 앱처럼 전체화면으로 실행
- 하단 탭바로 주요 기능 즉시 이동
  - 단어장 · 단어시험 · 어순연습 · 작문 · (더보기: 사전 / 대시보드 / 학습상담)
- 로고와 로그아웃만 있는 깔끔한 PWA 전용 상단바

---

## 🗂️ 프로젝트 구조

```
vocahigh/
├── create_app.py           # Flask 앱 팩토리
├── models/                 # SQLAlchemy ORM 모델
│   ├── user.py
│   ├── vocab_list.py
│   └── ...
├── blueprints/             # 기능별 Blueprint 분리
│   ├── auth/               # 로그인 · 회원가입
│   ├── vocab/              # 단어장
│   ├── quiz/               # 단어 시험
│   ├── wordorder/          # 어순 연습
│   ├── writing/            # 작문 (99번 · 100번)
│   ├── dictionary/         # 사전
│   ├── dashboard/          # 대시보드
│   ├── board/              # 학습 상담 게시판
│   └── main/               # 홈 · sw.js 서빙
├── templates/              # Jinja2 HTML 템플릿
├── static/
│   ├── css/style.css       # 커스텀 반응형 CSS
│   ├── sw.js               # Service Worker (PWA)
│   ├── manifest.json       # PWA 매니페스트
│   └── icons/              # PWA 아이콘 (192 · 512px)
└── requirements.txt
```

---

## 🛠 Tech Stack

| 구분 | V1 | V2 |
|:---|:---:|:---:|
| **Web Framework** | Streamlit | Flask 3.x |
| **아키텍처** | 단일 파일 | Blueprint MVC |
| **DB** | Google Sheets | MySQL + SQLAlchemy |
| **인증** | 별명 입력 | bcrypt + Flask-Login |
| **AI 모델** | GPT-4o, DALL-E 3 | GPT-4o, gpt-image-1.5 |
| **배포** | 로컬 | Railway 클라우드 |
| **모바일** | ❌ | 반응형 + PWA |

---

## ☁️ 배포

Railway 클라우드 위에서 MySQL과 함께 운영됩니다.

```
OPENAI_API_KEY=...
DATABASE_URL=mysql+pymysql://...
SECRET_KEY=...
```

환경변수만 설정하면 `railway up` 한 줄로 배포 완료.

---

## 🏁 마무리

V1은 **가능성의 증명**이었습니다.
V2는 **그 가능성이 실제 서비스가 된 결과**입니다.

혼자 공부하는 HSK 수험생이 AI를 손안의 과외 선생님처럼 쓸 수 있도록 —
voca海는 계속 헤엄칩니다. 🌊

---

<div align="center">
<sub>voca海 &copy; 2025 — HSK 수험생을 위한 AI 학습 도우미</sub>
</div>
