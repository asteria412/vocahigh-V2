# core/pdf_loader.py

import fitz  # PyMuPDF 라이브러리

def is_text_corrupted(text, threshold=0.2):
    """
    텍스트에 '깨진 글자(Replacement Character, 특수기호 등)'가 
    얼마나 많은지 비율을 측정합니다.
    
    Args:
        text (str): 분석할 텍스트
        threshold (float): 깨진 글자 비율 임계값 (기본 20% 이상이면 깨짐 판정)
        
    Returns:
        bool: 깨진 파일이면 True, 정상이면 False
    """
    if not text:
        return False
        
    total_chars = len(text)
    if total_chars == 0:
        return False

    # 깨진 글자로 의심되는 문자들 (: Replacement Character, □: 두부 문자)
    # 필요하면 여기에 감지하고 싶은 이상한 문자들을 더 추가하면 됩니다.
    corrupted_count = text.count('\ufffd') + text.count('□') + text.count('')
    
    ratio = corrupted_count / total_chars
    
    # 디버깅용 로그 (나중에 주석 처리 가능)
    # print(f"[DEBUG] 깨짐 비율: {ratio*100:.2f}% (임계값: {threshold*100}%)")
    
    return ratio > threshold

def load_text_from_pdf(uploaded_file) -> str:
    """
    업로드된 PDF 파일에서 텍스트를 추출합니다.
    * 기능 1: '2단 구성(다단)' 문서도 사람이 읽는 순서대로 정렬 (sort=True)
    * 기능 2: 텍스트 깨짐 감지 (OCR 필요 여부 판단용)
    """
    if uploaded_file is None:
        return ""

    try:
        # 1. 파일 열기
        file_bytes = uploaded_file.read()
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        
        full_text = ""

        # 2. 페이지별 텍스트 추출
        for page in doc:
            # sort=True: 2단 편집 문서 대응 (좌상->우하 순서 정렬)
            blocks = page.get_text("blocks", sort=True)
            
            for b in blocks:
                block_text = b[4] # 실제 텍스트
                full_text += block_text + "\n"
        
        doc.close()
        
        # 3. [추가된 기능] 텍스트가 정상인지 검사 (방사능 측정)
        if is_text_corrupted(full_text):
            print("⚠️ 경고: PDF 텍스트 추출 결과가 심하게 깨져 있습니다.")
            print("   (이 파일은 텍스트 복사 방지가 걸려있거나, 이미지 통파일일 수 있습니다.)")
            # 상황에 따라 여기서 에러 메시지를 리턴하거나, 
            # 나중에 OCR 로직을 태우기 위한 신호([CORRUPTED])를 줄 수 있습니다.
            return "[CORRUPTED_FILE] 텍스트가 깨져서 추출할 수 없습니다."

        return full_text

    except Exception as e:
        print(f"PDF 읽기 에러: {e}")
        return ""