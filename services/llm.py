# 경로: services/llm.py

import os, json
import pandas as pd
from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
import random 

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# =============================================================================
# [SECTION 1] 파싱된 단어 검증 및 빈칸 보정부
# =============================================================================

# [프롬프트 수정] 채우기가 아닌 '존재 증거 찾기'에 집중
SYSTEM_PROMPT = """
당신은 '단어장 무결성 검수자'입니다. 
파서가 추출한 항목이 원본 텍스트 내에서 실제 '단어'로서 유효한지 검증하세요.

[임무]
1. 제시된 한자가 원본 조각 내에서 단어-병음-뜻의 구조를 가진 '진짜 단어'인지 확인하세요.
2. 진짜라면 원본에 적힌 병음과 뜻을 정확히 추출하세요.
3. 만약 한자가 단어가 아닌 단순 텍스트(페이지 번호, 섹션 제목, 예문 파편 등)라면 반드시 is_noise: true로 응답하세요.

반드시 JSON으로 응답: {"zh": "한자", "pinyin": "병음", "ko": "뜻", "is_noise": false/true}
"""

def process_vocab_with_llm(df, raw_text):
    """
    df: 1차 파싱된 데이터 (개수 상관 없음)
    raw_text: PDF 전체 원본
    """
    if df.empty: return df
    
    # 1. 보정이 필요한 '빈칸 행'들만 핀포인트로 추출
    repair_targets = df[df['flags'] != 'OK'].copy()
    if repair_targets.empty: return df

    progress_bar = st.progress(0)
    indices_to_drop = [] # 노이즈(가짜 단어)로 판명된 행 보관함

    # 2. 유기적 대조 시작
    for i, (idx, row) in enumerate(repair_targets.iterrows()):
        target_zh = row['zh']
        
        # [원리] find()로 원본 내 '좌표' 확보하여 잽싸게 이동
        char_pos = raw_text.find(target_zh)
        
        if char_pos != -1:
            # 해당 단어 앞뒤 500자 조각(Context) 슬라이싱
            snippet = raw_text[max(0, char_pos-100) : min(len(raw_text), char_pos+400)]
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"검수 단어: {target_zh}\n원본 조각: {snippet}"}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0
                )
                res = json.loads(response.choices[0].message.content)
                
                # AI가 노이즈로 판별하면 삭제 리스트에 등록
                if res.get('is_noise') is True:
                    indices_to_drop.append(idx)
                else:
                    # 진짜 단어면 정보 업데이트 및 OK 부여
                    df.at[idx, 'pinyin'] = res.get('pinyin', row['pinyin'])
                    df.at[idx, 'ko'] = res.get('ko', row['ko'])
                    df.at[idx, 'flags'] = 'OK'
            except:
                pass
        else:
            # 원본에 한자 자체가 없으면 유령 데이터이므로 삭제
            indices_to_drop.append(idx)
        
        progress_bar.progress((i + 1) / len(repair_targets))

    # 3. [최종 정제] 가짜 단어들을 쳐내어 개수를 원본에 맞게 수렴시킴
    if indices_to_drop:
        df = df.drop(indices_to_drop)
        df = df.reset_index(drop=True)

    return df


# =============================================================================
# [SECTION 2] 어순 배열 문제 출제부
# =============================================================================

# [수정] level 변수를 추가하여 HSK 4급~6급 모두 대응 가능하도록 변경

def generate_sentence_puzzle(selected_words, level="HSK5"):
    """
    선택된 단어를 사용하여 지정된 레벨(기본 HSK5)의 어순 배열 문제를 생성합니다.
    level 인자를 통해 "HSK4", "HSK6" 등으로 난이도 조절이 가능합니다.
    """
    if not client:
        return None

    joined_words = ", ".join(selected_words)
    
    # 3가지 출제 전략 (레벨에 상관없이 통용되는 문법 구조)
    strategies = [
        {
            "type": "Collocation Focus (호응 관계)",
            "instruction": f"""
            1. 선택된 단어와 어울리는 **{level} 필수 호응구(Collocation)**를 포함하여 문장을 만드세요.
            2. 단어 조각을 나눌 때, 이 호응하는 단어들을 **반드시 떨어뜨려 놓으세요**.
            3. 사용자가 의미가 아닌 '구조적 짝꿍'을 찾아야 풀 수 있게 하세요.
            """
        },
        {
            "type": "Complex Syntax (복잡한 수식어)",
            "instruction": """
            1. 주어(S)나 목적어(O)를 꾸며주는 **긴 관형어(Phrase + 的)**가 포함된 문장을 만드세요.
            2. 단순한 '형용사+명사'가 아니라, '동사구+的+명사' 형태를 사용하세요.
            3. 단어 조각을 나눌 때, **'的'와 '피수식 명사'를 분리**하세요.
            """
        },
        {
            "type": "Logical Connection (접속사/논리)",
            "instruction": """
            1. 문장의 논리를 결정하는 **접속사(因此, 但是, 甚至, 否则 등)**를 하나 이상 포함하세요.
            2. 앞뒤 절의 인과관계나 전환 관계가 명확한 복문을 만드세요.
            3. 사용자가 문맥의 흐름을 타야만 순서를 맞출 수 있게 하세요.
            """
        }
    ]
    
    selected_strategy = random.choice(strategies)

    # [수정 포인트] 프롬프트 내 'HSK 5급' -> '{level}' 변수로 교체
    prompt = f"""
    당신은 2025년 최신 경향을 반영하는 {level} 출제위원입니다.
    사용자 선택 단어: {joined_words}
    
    [이번 문제의 출제 전략]: {selected_strategy['type']}
    {selected_strategy['instruction']}

    [공통 요구사항]
    1. 문장은 **{level} 수준**이어야 하며, 해당 급수의 지정 어휘를 최대한 활용하세요.
    2. 생성된 문장을 4~6개의 의미 단위(단어 조각)로 나누세요.
    3. 한국어 해석은 직역보다 자연스러운 의역으로 제공하세요.

    [출력 형식 - JSON Only]
    {{
        "chinese": "완성된 중국어 문장",
        "pinyin": "병음",
        "korean": "한국어 해석",
        "pieces": ["조각1", "조각2", "조각3", "조각4", "조각5"],
        "grammar_point": "핵심 문법 포인트 설명"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "당신은 JSON 데이터를 생성하는 전문가입니다."},
                      {"role": "user", "content": prompt}],
            temperature=0.7 
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "")
        
        import json
        return json.loads(content)
    except Exception as e:
        print(f"Error generating puzzle: {e}")
        return None


# =============================================================================
# [SECTION 3] 실전 작문부
# =============================================================================
# 1. 99번(제시어): 내 단어장 + 트렌드 단어(명사 중심) 하이브리드 출제
# 2. 100번(그림): 4대 빈출 테마(비즈니스/일상/여가/학습) 기반 상황 묘사 및 이미지 생성
# 3. 평가(채점): 기본 점수(80점) 시작 + 가점(고급표현) / 감점(논리오류) 로직
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# [3-1] 작문 문제 출제 (Question Generation)
# -----------------------------------------------------------------------------

def generate_hybrid_question_99(user_vocab_list):
    """
    [99번 출제: 하이브리드 믹스]
    - 사용자 단어(3개)와 2025 트렌드 단어(2개)를 결합하여 출제합니다.
    - 단순 예시 나열이 아닌, '4대 의미 클러스터' 정의를 바탕으로 AI가 맥락에 맞는 단어를 창조합니다.
    """
    if not client:
        return None
    
    # 1. 사용자 단어장에서 3개 무작위 추출 (기반 단어)
    if len(user_vocab_list) >= 3:
        picked_words = random.sample(user_vocab_list, 3)
    else:
        picked_words = user_vocab_list
    
    picked_text = ", ".join([w['zh'] for w in picked_words])

    # 2. 2025 트렌드 지식 주입 (AI가 참고할 정의)
    trend_knowledge = """
    [2025 HSK 5급 출제 트렌드 - 4대 의미 클러스터]
    1. **Cluster A (디지털/라이프):** - 정의: 스마트폰, 앱, 온라인 활동, 현대인의 여가, 전자기기.
       - 키워드 느낌: 오디오북(听书), 브이로그, 알고리즘, 배터리, 시차, 가상현실 등.
    2. **Cluster B (비즈니스/행정):** - 정의: 회사 업무, 서류 처리, 계약, 협상, 공식 절차.
       - 키워드 느낌: 영업집조(营业执照), 영수증(发票), 계약서, 예산, 협상, 승인하다 등.
    3. **Cluster C (캠퍼스/학습):** - 정의: 대학 생활, 수강 신청, 학점, 논문, 동아리.
       - 키워드 느낌: 개설하다(开设), 필수과목, 멘토, 장학금, 무술(동아리), 모집하다 등.
    4. **Cluster D (문제해결/DIY):** - 정의: 조립, 수리, 인테리어, 디자인 등 구체적 행위.
       - 키워드 느낌: 조립하다(组装), 설명서, 부품, 치수, 꼼꼼하다(用心), 개조하다 등.
    """

    # 3. 프롬프트 생성
    prompt = f"""
    당신은 창의적인 HSK 5급 출제위원입니다.
    학습자의 단어 3개를 분석하고, 위 [4대 의미 클러스터] 중 가장 잘 어울리는 테마 하나를 골라 
    최신 트렌드 단어 2개를 추가하여 총 5개의 제시어 세트를 만드세요.

    [학습자 단어 (필수 포함)]
    {picked_text}

    [출제 조건]
    1. 학습자 단어의 맥락(Context)을 파악하여 가장 자연스러운 클러스터를 선택하세요.
    2. 선택된 클러스터의 정의에 부합하는 **2025년형 최신 명사/동사 2개**를 생성하세요.
    3. 5개 단어가 쌩뚱맞지 않고 하나의 **'말이 되는 상황(Scenario)'**으로 연결되어야 합니다.

    [출력 형식 - JSON Only]
    {{
        "theme": "선택된 클러스터 테마 (예: 비즈니스 협상)",
        "words": [
            {{"zh": "학습자단어1", "pinyin": "...", "ko": "...", "pos": "...", "source": "내단어장"}},
            {{"zh": "학습자단어2", "pinyin": "...", "ko": "...", "pos": "...", "source": "내단어장"}},
            {{"zh": "학습자단어3", "pinyin": "...", "ko": "...", "pos": "...", "source": "내단어장"}},
            {{"zh": "AI생성단어1", "pinyin": "...", "ko": "...", "pos": "...", "source": "AI트렌드"}},
            {{"zh": "AI생성단어2", "pinyin": "...", "ko": "...", "pos": "...", "source": "AI트렌드"}}
        ]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "JSON 생성 전문가입니다."},
                      {"role": "user", "content": prompt}],
            temperature=0.8 # 다양성을 위해 온도 높임
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"Error generating hybrid question: {e}")
        return None


def generate_scene_description(level="HSK5"):
    """
    [100번 출제: 테마별 전략 반영]
    - 딥리서치 기준 4대 빈출 테마(비즈니스/일상/스포츠/학습) 내에서 상황을 무작위 선정.
    - 각 테마별 '공략 가이드(Guide)'를 프롬프트에 반영하여, 작문하기 좋은 최적의 상황 묘사를 생성.
    """
    if not client:
        return None

    # [전략 데이터] 테마별 세부 상황 및 출제 가이드
    theme_strategies = {
        "비즈니스/오피스": {
            "sub_topics": [
                "채용 면접을 보는 상황 (인재, 장점)",
                "계약서에 서명하는 상황 (계약, 체결)",
                "회의실에서 프레젠테이션 하는 상황 (발표, 데이터)",
                "상사에게 업무 보고를 하는 상황 (보고, 수정)",
                "동료와 악수하며 협력을 약속하는 상황 (협력, 기회)"
            ],
            "guide": "격식체 어휘(Formal vocabulary)를 사용하고, 업무적인 분위기를 묘사하세요."
        },
        "일상/가사": {
            "sub_topics": [
                "주방에서 요리하다가 실수한 상황 (재료, 소금)",
                "대청소를 하며 가구를 옮기는 상황 (정리, 깨끗하다)",
                "마트에서 물건을 고르며 가격을 비교하는 상황 (가격, 품질)",
                "이사짐을 싸거나 푸는 상황 (이사, 박스)",
                "고장 난 물건을 수리하는 상황 (수리, 기계)"
            ],
            "guide": "일상적인 어휘를 사용하고, '경험담(만능 서사)'을 적용하기 쉬운 상황을 묘사하세요."
        },
        "스포츠/여가": {
            "sub_topics": [
                "강가에서 낚시를 하며 기다리는 상황 (인내심, 월척)",
                "산 정상에 올라가 풍경을 바라보는 상황 (등산, 성취감)",
                "헬스장에서 땀 흘리며 운동하는 상황 (건강, 근육)",
                "공원에서 강아지와 산책하거나 조깅하는 상황 (산책, 활기)",
                "경기장에서 시합을 응원하는 상황 (응원, 승리)"
            ],
            "guide": "구체적인 '동작 동사'를 사용하고, 인물의 '상태'가 드러나게 묘사하세요."
        },
        "학습/독서": {
            "sub_topics": [
                "도서관에서 책을 찾거나 읽는 상황 (자료, 지식)",
                "밤늦게까지 스탠드를 켜고 공부하는 상황 (노력, 피곤)",
                "졸업식에서 학위복을 입고 사진 찍는 상황 (졸업, 미래)",
                "서점에서 마음에 드는 책을 발견한 상황 (취미, 작가)",
                "노트북으로 논문이나 과제를 작성하는 상황 (입력, 저장)"
            ],
            "guide": "'집중(集中)', '노력(努力)'과 관련된 어휘가 자연스럽게 떠오르도록 학구적인 분위기를 묘사하세요."
        }
    }

    # 1. 테마 및 세부 상황 랜덤 선택
    selected_category = random.choice(list(theme_strategies.keys()))
    strategy = theme_strategies[selected_category]
    selected_sub_topic = random.choice(strategy['sub_topics'])

    prompt = f"""
    당신은 2025년 경향을 반영하는 HSK {level} 작문 출제위원입니다.
    
    [출제 테마]: {selected_category}
    [구체적 상황]: {selected_sub_topic}
    [출제 전략]: {strategy['guide']}
    
    [미션]
    1. 위 상황을 바탕으로 100번 문제(그림 작문) 텍스트를 묘사하세요. (한국어로)
    2. 사진이 없어도 머릿속에 그림이 그려지도록 인물의 행동과 표정을 구체적으로 묘사하세요.
    3. 해당 상황에 꼭 필요한 HSK 5급 핵심 단어(중국어) 2개를 힌트로 추출하세요.

    [출력 형식 - JSON Only]
    {{
        "scene_desc": "상황 묘사 텍스트",
        "keywords": ["단어1", "단어2"]
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "당신은 JSON 데이터를 생성하는 전문가입니다."},
                      {"role": "user", "content": prompt}],
            temperature=0.8 # 창의적인 상황 생성을 위해 온도를 약간 높임
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "")
        return json.loads(content)
    except Exception as e:
        print(f"Error generating scene: {e}")
        return None

def generate_image_from_text(description):
    """
    [이미지 생성] 텍스트 묘사를 바탕으로 DALL-E 3 이미지를 생성합니다.
    """
    if not client:
        return None
    
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=f"A realistic illustration for a Chinese language proficiency test (HSK). Scene: {description}. Clean style, no text inside image.",
            size="1024x1024",
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# -----------------------------------------------------------------------------
# [3-2] 작문 채점 및 평가 (Evaluation)
# -----------------------------------------------------------------------------

# [통합 채점] HSK 공식 기준(상/중/하) + 거품 뺀 가산점 로직 (Base 75)

def evaluate_writing_v2(mode, user_input, ref_data):
    """
    [통합 채점 로직]
    1. 공식 평가 기준(High/Mid/Low)은 원문 그대로 유지.
    2. 점수 산정 방식 (거품 제거):
        - 무결점이지만 평이한 답안 = 75점(중상) 시작. (기존 80점에서 하향)
        - 80점 이상은 '제시어 외 고급 어휘'나 '복잡한 문형'이 있을 때만 부여.
        - 비상식적 내용(논리 오류)은 가차 없이 강등.
    """
    if not client:
        return None

    # ---------------------------------------------------------
    # 1. 문제별 평가 기준 (공식 원문 유지)
    # ---------------------------------------------------------
    if mode == '99':
        condition = f"필수 포함 단어 5개: {', '.join(ref_data)}"
        
        # [99번 공식 기준 원문]
        criteria_guide = """
        [평가 등급 기준]
        1. 상 (높은 점수, 80~100점): 
            - 5개 어휘 전부 사용.
            - 어법 오류 없음.
            - 내용이 풍부하고 연결이 자연스러우며 논리적임.
        2. 중 (중간 점수, 60~79점): 
            - 5개 어휘 전부 사용.
            - 내용 연결은 되나 어법 오류/오타가 있거나, 문장이 단순함.
        3. 하 (낮은 점수, 0~59점): 
            - 5개 어휘 미사용(가장 큰 감점).
            - 내용이 연결되지 않거나(비논리적), 어법 오류가 많음.
            - 비워둔 경우 0점.
        """
        
    else: # 100번
        condition = f"사진 상황 묘사: {ref_data}"
        
        # [100번 공식 기준 원문]
        criteria_guide = """
        [평가 등급 기준]
        1. 상 (높은 점수, 80~100점): 
            - 내용과 그림의 연관성이 높음.
            - 어법 오류 없음.
            - 내용이 풍부하고 흐름이 자연스러우며 논리적임.
        2. 중 (중간 점수, 60~79점): 
            - 내용과 그림은 연관되나 어법 오류/오타가 있음.
            - 혹은 분량이 부족하거나 표현이 단순함.
        3. 하 (낮은 점수, 0~59점): 
            - 내용과 그림의 상관성이 적음 (엉뚱한 내용).
            - 어법 오류가 많거나 문장이 성립되지 않음.
            - 비워둔 경우 0점.
        
        * 주의: 자신의 견해나 심리 묘사는 평가 요소가 아님. '규범성(어법)'과 '유창성'에 집중할 것.
        """

    # ---------------------------------------------------------
    # 2. 채점 가이드라인 (거품 제거 & 로직 강화)
    # ---------------------------------------------------------
    prompt = f"""
    당신은 **매우 깐깐한 HSK 5급 공식 채점관**입니다.
    위의 [평가 등급 기준]을 바탕으로, 아래 [점수 결정 로직] 프로세스를 엄격히 따라 점수를 산정하세요.
    **점수 인플레이션(거품)을 경계하세요.**

    [문제 정보 - {mode}번 유형]
    {condition}
    
    [학생 답안]
    {user_input}

    {criteria_guide}

    [점수 결정 로직 - Step by Step]
    
    **1단계: 기본 등급 결정 (Base Score: 75점)**
    - 조건: 5개 단어 사용(99번) / 그림 연관성 있음(100번).
    - **CASE A (무결점 평이):** 문법 오류가 없고 논리가 맞지만, 문장이 단순하다 -> **75점 (중상)** 부여. (절대 80점 주지 마세요)
    - **CASE B (부족):** 문법 오류가 있거나 문장이 너무 단순하다 -> **60~69점 (중하)** 부여.
    - **CASE C (미달):** 필수 단어 누락 / 그림과 무관 / 심각한 비문 -> **50점 미만 (하)**.

    **2단계: 고득점 승격 심사 (Bonus Point)**
    - 1단계에서 75점을 받은 답안에 한해, 아래 요소가 있을 때만 점수를 더하세요.
        ① **제시어 외 고급 어휘:** 주어진 5개 단어 말고, 추가적으로 5급/6급 수준의 어휘/성어를 썼는가? (+5점)
        ② **고급 문형:** '把/被' 자문, 반어문, 이중부정 등 복잡한 문장 구조를 썼는가? (+5점)
        ③ **접속사 활용:** (因此, 不仅...而且..., 即使 등) 문장 간의 연결이 매우 유려한가? (+5점)
    
    * 주의: 제시된 단어 5개를 쓴 건 당연한 의무이므로 가산점 사유가 아닙니다.

    **3단계: 논리 검증 및 강등 (Safety Check)**
    - 문법이 맞아도 **'비상식적 내용(예: 빨간 사자, 방을 열애하다)'**이 발견되면 -> **무조건 [중] 등급(70점 이하)으로 강등**시키세요.
    - 100번에서 단순 나열(CCTV식 묘사)만 있다면 -> **최대 70점**으로 제한하세요.

    [출력 형식 - JSON Only]
    {{
        "score": 78 (0~100점 사이 정수),
        "correction": "고급 문형과 어휘를 보강하여 90점 이상 받을 수 있는 모범 답안 (중국어)",
        "translation": "모범 답안의 한국어 해석",
        "explanation": "점수 산정 근거 (예: '문법 오류가 없어 기본점 75점입니다. 제시어 외에 고급 어휘 사용이 부족하여 80점을 넘지 못했습니다.')",
        "better_expression": "점수를 85점 이상으로 올리기 위한 추천 어휘/접속사"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "JSON 생성 전문가입니다."},
                      {"role": "user", "content": prompt}],
            temperature=0.2 # 온도를 낮춰서 냉정한 평가 유도
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "")
        import json
        return json.loads(content)
    except Exception as e:
        print(f"Error evaluating writing v2: {e}")
        return None

# =============================================================================
# [SECTION 4] AI 단어사전부
# [단어사전] 한국어 검색어(아끼다)가 들어오면 -> 적절한 중국어(爱惜/节约)로 변환해서 검색
# =============================================================================

def search_word_info(word):
    """
    [단어 사전 기능] 
    사용자가 입력한 단어(중국어 or 한국어)를 분석하여
    최적의 중국어 단어 정보를 JSON으로 반환합니다.
    """
    if not client:
        return None

    prompt = f"""
    당신은 중국어 학습용 AI 사전입니다.
    사용자가 입력한 검색어: '{word}'
    
    [지시사항]
    1. **입력값이 중국어(한자)인 경우:** 해당 단어의 정보를 바로 작성하세요.
    2. **입력값이 한국어인 경우:** 해당 뜻을 가진 **가장 적절한 HSK 5급 수준의 중국어 단어** 하나를 선정하여 그 단어의 정보를 작성하세요.
       (예: '아끼다' 입력 시 -> '爱惜' 또는 '节约' 중 문맥상 5급에 적합한 것 선택)

    [필수 포함 항목]
    1. word: 검색된 중국어 단어 (한자)
    2. pinyin: 병음 (성조 표시 포함)
    3. pos: 품사 (예: 명사, 동사, 형용사 등)
    4. meaning: 한국어 뜻 (핵심 의미)
    5. example_cn: HSK 5급 수준의 중국어 예문 1개
    6. example_kr: 예문의 한국어 해석
    
    [출력 형식 - JSON Only]
    {{
        "word": "중국어단어",
        "pinyin": "bīnyīn",
        "pos": "품사",
        "meaning": "한국어 뜻",
        "example_cn": "중국어 예문",
        "example_kr": "예문 해석"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "JSON 데이터 생성기입니다."},
                      {"role": "user", "content": prompt}],
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "")
        
        import json
        return json.loads(content)
    except Exception as e:
        print(f"Error searching word info: {e}")
        return None