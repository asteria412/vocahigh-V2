# core/vocab_parser.py

import re
import unicodedata
import pandas as pd

# ==========================================
# 1. 기준 데이터
# ==========================================

PINYIN_WHITELIST = {
    "a", "ai", "an", "ang", "ao", "ba", "bai", "ban", "bang", "bao", "bei", "ben", "beng", "bi", "bian", "biao", "bie", "bin", "bing", "bo", "bu",
    "ca", "cai", "can", "cang", "cao", "ce", "cen", "ceng", "cha", "chai", "chan", "chang", "chao", "che", "chen", "cheng", "chi", "chong", "chou", "chu", "chua", "chuai", "chuan", "chuang", "chui", "chun", "chuo", "ci", "cong", "cou", "cu", "cuan", "cui", "cun", "cuo",
    "da", "dai", "dan", "dang", "dao", "de", "dei", "den", "deng", "di", "dian", "diao", "die", "ding", "diu", "dong", "dou", "du", "duan", "dui", "dun", "duo",
    "e", "ei", "en", "eng", "er", "fa", "fan", "fang", "fei", "fen", "feng", "fo", "fou", "fu",
    "ga", "gai", "gan", "gang", "gao", "ge", "gei", "gen", "geng", "gong", "gou", "gu", "gua", "guai", "guan", "guang", "gui", "gun", "guo",
    "ha", "hai", "han", "hang", "hao", "he", "hei", "hen", "heng", "hong", "hou", "hu", "hua", "huai", "huan", "huang", "hui", "hun", "huo",
    "ji", "jia", "jian", "jiang", "jiao", "jie", "jin", "jing", "jiong", "jiu", "ju", "juan", "jue", "jun",
    "ka", "kai", "kan", "kang", "kao", "ke", "kei", "ken", "keng", "kong", "kou", "ku", "kua", "kuai", "kuan", "kuang", "kui", "kun", "kuo",
    "la", "lai", "lan", "lang", "lao", "le", "lei", "leng", "li", "lia", "lian", "liang", "liao", "lie", "lin", "ling", "liu", "long", "lou", "lu", "luan", "lun", "luo", "lü", "lue",
    "ma", "mai", "man", "mang", "mao", "me", "mei", "men", "meng", "mi", "mian", "miao", "mie", "min", "ming", "miu", "mo", "mou", "mu",
    "na", "nai", "nan", "nang", "nao", "ne", "nei", "nen", "neng", "ni", "nian", "niang", "niao", "nie", "nin", "ning", "niu", "nong", "nou", "nu", "nuan", "nuo", "nü", "nue",
    "o", "ou", "pa", "pai", "pan", "pang", "pao", "pei", "pen", "peng", "pi", "pian", "piao", "pie", "pin", "ping", "po", "pou", "pu",
    "qi", "qia", "qian", "qiang", "qiao", "qie", "qin", "qing", "qiong", "qiu", "qu", "quan", "que", "qun",
    "ran", "rang", "rao", "re", "ren", "reng", "ri", "rong", "rou", "ru", "rua", "ruan", "rui", "run", "ruo",
    "sa", "sai", "san", "sang", "sao", "se", "sen", "seng", "sha", "shai", "shan", "shang", "shao", "she", "shei", "shen", "sheng", "shi", "shou", "shu", "shua", "shuai", "shuan", "shuang", "shui", "shun", "shuo", "si", "song", "sou", "su", "suan", "sui", "sun", "suo",
    "ta", "tai", "tan", "tang", "tao", "te", "teng", "ti", "tian", "tiao", "tie", "ting", "tong", "tou", "tu", "tuan", "tui", "tun", "tuo",
    "wa", "wai", "wan", "wang", "wei", "wen", "weng", "wo", "wu",
    "xi", "xia", "xian", "xiang", "xiao", "xie", "xin", "xing", "xiu", "xiong", "xu", "xuan", "xue", "xun",
    "ya", "yan", "yang", "yao", "ye", "yi", "yin", "ying", "yong", "you", "yu", "yuan", "yue", "yun",
    "za", "zai", "zan", "zang", "zao", "ze", "zei", "zen", "zeng", "zha", "zhai", "zhan", "zhang", "zhao", "zhe", "zhei", "zhen", "zheng", "zhi", "zhong", "zhou", "zhu", "zhua", "zhuai", "zhuan", "zhuang", "zhui", "zhun", "zhuo", "zi", "zong", "zou", "zu", "zuan", "zui", "zun", "zuo"
}

POS_SET = {"명사", "동사", "형용사", "부사", "개사", "접속사", "조사", "양사", "대명사", "수사", "감탄사", "의성어", "명", "동", "형", "부", "개", "접", "조", "양", "대", "수", "감", "vi", "vt", "n", "v", "adj", "adv"}

HANZI_ANCHOR_RE = re.compile(r"(?:\d+[\.\)]\s*)?(?P<zh>[\u4e00-\u9fff]+)")
TONE_CHARS_RE = re.compile(r"[āáǎàēéěèīíǐìōóǒòūúǔùüǖǘǚǜ]")
GARBAGE_ROW_RE = re.compile(r"[\u2460-\u2473\u24D0-\u24E9]|정답|보기|해설")
INSTRUCTION_KEYWORDS = ["하세요", "하시오", "찾아", "연결", "맞는", "고르", "다음", "알맞은"]


# ★(중요도), ※(참고), □(체크박스), ■(채워진박스) 등
HACKERS_NOISE_RE = re.compile(r"^[★☆※□■\u2600-\u26FF\u2700-\u27BF]+$")

# ==========================================
# 2. 로직
# ==========================================

def is_korean_char(char):
    code = ord(char)
    return (0xAC00 <= code <= 0xD7A3) or (0x3130 <= code <= 0x318F)

def cut_tail_after_last_korean(text):
    if not text: return ""
    
    # [업데이트] 앞쪽 청소에 '※' 추가 (뜻 앞에 붙는 기호 제거)
    text = re.sub(r"^[\s\*\-\.\•\·\~※]+", "", text)
    text = re.sub(r"^\d+급\s*", "", text)

    last_korean_idx = -1
    for i in range(len(text) - 1, -1, -1):
        if is_korean_char(text[i]):
            last_korean_idx = i
            break
            
    if last_korean_idx == -1:
        return re.sub(r"[\s≠≈=\*_\.ㅁ□■△▲○●]+$", "", text)
    
    return text[:last_korean_idx+1].strip()


def clean_chunk_content(text):
    if not text: return "", "", ""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\[\]\(\)\<\>,\.\-\~]", " ", text) 
    tokens = text.split()
    
    pinyin_list, pos_list, meaning_list = [], [], []
    
    for token in tokens:
        token = token.strip()
        if not token: continue
        
        # [업데이트] 해커스 노이즈 토큰(★, □ 등) 발견 시 즉시 건너뜀
        if HACKERS_NOISE_RE.match(token):
            continue
        
        # 1. 병음 판단
        if TONE_CHARS_RE.search(token):
            pinyin_list.append(token)
            continue
            
        # 2. 성조 없는 알파벳
        if re.match(r"^[a-zA-ZüÜ:]+$", token):
            low_token = token.lower().replace(':', 'ü')
            if low_token in PINYIN_WHITELIST:
                pinyin_list.append(token)
                continue
            if token in POS_SET:
                if token not in pos_list: pos_list.append(token)
                continue
            continue 
            
        # 3. 한글 품사
        if token in POS_SET:
            if token not in pos_list: pos_list.append(token)
            continue

        meaning_list.append(token)

    final_ko = " ".join(meaning_list)
    
    for kw in INSTRUCTION_KEYWORDS:
        if kw in final_ko:
            final_ko = ""
            break

    cleaned_ko = cut_tail_after_last_korean(final_ko)

    return " ".join(pinyin_list), ", ".join(dict.fromkeys(pos_list)), cleaned_ko

# ==========================================
# 3. 메인 파서
# ==========================================

def parse_text_by_chunks(full_text, level, source):
    rows = []
    matches = list(HANZI_ANCHOR_RE.finditer(full_text))
        
    for i, curr_match in enumerate(matches):
        zh_word = curr_match.group("zh")
        if len(zh_word) >= 5: continue
        
        start_idx = curr_match.end()
        end_idx = matches[i+1].start() if i < len(matches)-1 else len(full_text)
        
        pinyin, pos, ko = clean_chunk_content(full_text[start_idx:end_idx])
        
        if GARBAGE_ROW_RE.search(ko): continue

        flags = []
        if not pinyin: flags.append("NO_PINYIN")
        if not ko: flags.append("NO_MEANING")
            
        rows.append({
            "zh": zh_word, 
            "pinyin": pinyin, 
            "ko": ko, 
            "pos": pos, 
            "flags": " | ".join(flags) if flags else "OK",
            "level": level,
            "source": source
        })

    return pd.DataFrame(rows)

def change_text_to_vocab_df(extracted_text, level="HSK", source="generic", use_llm=False):
    df = parse_text_by_chunks(extracted_text, level, source)
    if df.empty: 
        return pd.DataFrame(columns=["zh", "pinyin", "ko", "pos", "flags"])
    return df[["zh", "pinyin", "ko", "pos", "flags"]]