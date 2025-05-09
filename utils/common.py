import os
import json
import re

# --- 디렉토리 경로 상수 ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 프로젝트 루트
DATA_DIR = os.path.join(BASE_DIR, "data")

OCR_RESULT_PATH = os.path.join(DATA_DIR, "ocr_result.json")
OCR_TOKENS_PATH = os.path.join(DATA_DIR, "ocr_tokens.json")
OCR_TOKENS_FILTERED_PATH = os.path.join(DATA_DIR, "ocr_tokens_filtered.json")
OCR_TOKENS_FROM_TABLE_PATH = os.path.join(DATA_DIR, "ocr_tokens_from_table.json")
OCR_TOKENS_FROM_TEXT_PATH = os.path.join(DATA_DIR, "ocr_tokens_from_text.json")
LABEL_KEYWORDS_PATH = os.path.join(DATA_DIR, "label_keywords.json")

# --- 문서 유형 판단 함수 ---
def detect_doc_type(tokens):
    for token in tokens:
        if token in {"이력서", "재직증명서", "위임장", "자기소개서", "일일업무보고서", "일일업무일지"}:
            return {
                "이력서": "resume",
                "재직증명서": "certificate",
                "위임장": "consent",
                "자기소개서": "self_intro",
                "일일업무보고서": "report",
                "일일업무일지": "report"
            }[token]
    return None

# --- bbox 정규화 함수 ---
def normalize_bbox(vertices, img_w, img_h):
    x0 = int(vertices[0]['x'] * 1000 / img_w)
    y0 = int(vertices[0]['y'] * 1000 / img_h)
    x1 = int(vertices[2]['x'] * 1000 / img_w)
    y1 = int(vertices[2]['y'] * 1000 / img_h)
    return [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]

def save_json(filename: str, data: dict):
    if not filename.endswith(".json"):
        filename += ".json"
    path = os.path.join(DATA_DIR, filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json(filename: str):
    if not filename.endswith(".json"):
        filename += ".json"
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def remove_number_dot_prefix(text: str) -> str:
    return re.sub(r'^\d+\.', '', text)

def remove_spaces_from_tokens(tokens):
    return [token.replace(" ", "") for token in tokens]

def group_lines_by_y(bboxes, tolerance=5):
    y_groups = []
    norm_y_map = {}
    for box in bboxes:
        y = box[1]
        found = False
        for ref_y in y_groups:
            if abs(ref_y - y) <= tolerance:
                norm_y_map[y] = ref_y
                found = True
                break
        if not found:
            y_groups.append(y)
            norm_y_map[y] = y
    return norm_y_map

def group_lines_by_y_for_filter(bboxes, tolerance=5):
    lines = {}
    for i, box in enumerate(bboxes):
        y1 = box[1]
        found = False
        for ref_y in lines:
            if abs(ref_y - y1) <= tolerance:
                lines[ref_y].append(i)
                found = True
                break
        if not found:
            lines[y1] = [i]
    return lines
