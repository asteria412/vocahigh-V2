# =====================================================================
# run.py - Flask V2 서버 실행 파일
# =====================================================================
# 터미널에서 `python run.py` 로 실행해.
# V1의 app.py(Streamlit)와 구분하기 위해 run.py로 이름 지음.
# =====================================================================

from create_app import create_app

# 앱 생성 (개발 모드)
app = create_app('development')

if __name__ == '__main__':
    # debug=True: 코드 수정 시 서버 자동 재시작, 에러 메시지 상세 표시
    # port=5000: http://localhost:5000 으로 접속
    app.run(debug=True, port=5000)
