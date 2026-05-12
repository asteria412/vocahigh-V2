# 텍스트로 바꿔주는 함수 
def change_text_from_upload(uploaded_file) -> str:
    """
    Streamlit UploadedFile(PDF/TXT)를 받아서 text(str)로 반환
    """
    if uploaded_file is None:
        return ""

    # TXT
    if uploaded_file.type == "text/plain" or uploaded_file.name.lower().endswith(".txt"):
        return uploaded_file.getvalue().decode("utf-8", errors="ignore")

    # PDF
    if uploaded_file.type == "application/pdf" or uploaded_file.name.lower().endswith(".pdf"):
        # PyMuPDF: 환경에 따라 pymupdf / fitz 차이 처리
        try:
            import pymupdf as fitz
        except Exception:
            import fitz

        # UploadedFile은 bytes로 읽을 수 있음
        pdf_bytes = uploaded_file.getvalue()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        full_text = []
        for page in doc:
            full_text.append(page.get_text())
        return "\n".join(full_text)

    # 그 외
    return ""
