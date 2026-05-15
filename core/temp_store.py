import json
import os
import time
import uuid

TEMP_DIR = os.path.join(os.path.dirname(__file__), '..', 'tmp_vocab')
os.makedirs(TEMP_DIR, exist_ok=True)


def save_temp(prefix, data):
    key = str(uuid.uuid4())
    path = os.path.join(TEMP_DIR, f'{prefix}_{key}.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    return key


def load_temp(prefix, key):
    if not key:
        return None
    path = os.path.join(TEMP_DIR, f'{prefix}_{key}.json')
    if not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def delete_temp(prefix, key):
    if not key:
        return
    path = os.path.join(TEMP_DIR, f'{prefix}_{key}.json')
    if os.path.exists(path):
        os.remove(path)


def cleanup_old_temps(max_age_seconds=3600):
    """1시간 이상 된 임시 파일 자동 삭제"""
    now = time.time()
    for filename in os.listdir(TEMP_DIR):
        if not filename.endswith('.json'):
            continue
        path = os.path.join(TEMP_DIR, filename)
        try:
            if now - os.path.getmtime(path) > max_age_seconds:
                os.remove(path)
        except OSError:
            pass
