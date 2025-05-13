import json
from utils.common import (
    normalize_bbox, load_json, detect_doc_type, group_lines_by_y_for_filter, save_json
)
Y_TOL = 5
BLANK_TOKEN = "[BLANK]"

def is_date_unit(token):
    return token in {"년", "월", "일"}

def is_digit_str(token):
    return token.isdigit()

def is_in_table(bbox, table_boxes):
    x0, y0, x1, y1 = bbox
    for tx0, ty0, tx1, ty1 in table_boxes:
        if not (x1 < tx0 or x0 > tx1 or y1 < ty0 or y0 > ty1):
            return True
    return False

def blank_date_line_digits(tokens, bboxes, lines_by_y):
    blank_indices = set()
    for y, indices in lines_by_y.items():
        if any(tokens[idx] in {"년", "월", "일"} for idx in indices):
            for idx in indices:
                if tokens[idx].isdigit():
                    blank_indices.add(idx)
    return blank_indices

def merge_inline_blanks(tokens, bboxes, date_y_set, y_tol=5, max_gap=30):
    merged_tokens, merged_bboxes = [], []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        bbox = bboxes[i]
        if token == BLANK_TOKEN and any(abs(bbox[1] - y) <= y_tol for y in date_y_set):
            merged_bbox = bbox.copy()
            j = i + 1
            while (
                j < len(tokens)
                and tokens[j] == BLANK_TOKEN
                and abs(bboxes[j][1] - bbox[1]) <= y_tol
                and bboxes[j][0] - merged_bbox[2] <= max_gap
            ):
                next_bbox = bboxes[j]
                merged_bbox = [
                    min(merged_bbox[0], next_bbox[0]),
                    min(merged_bbox[1], next_bbox[1]),
                    max(merged_bbox[2], next_bbox[2]),
                    max(merged_bbox[3], next_bbox[3]),
                ]
                j += 1
            merged_tokens.append(BLANK_TOKEN)
            merged_bboxes.append(merged_bbox)
            i = j
        else:
            merged_tokens.append(token)
            merged_bboxes.append(bbox)
            i += 1
    return merged_tokens, merged_bboxes

def inject_blank_between_colon_and_seal(tokens, bboxes):
    result_tokens, result_bboxes = [], []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        bbox = bboxes[i]
        if token == ":":
            j = i + 1
            found = False
            while j < len(tokens):
                if tokens[j] == "(인)":
                    found = True
                    break
                j += 1
            if found and j > i + 1:
                merged_bbox = bboxes[i + 1]
                for k in range(i + 2, j):
                    merged_bbox = [
                        min(merged_bbox[0], bboxes[k][0]),
                        min(merged_bbox[1], bboxes[k][1]),
                        max(merged_bbox[2], bboxes[k][2]),
                        max(merged_bbox[3], bboxes[k][3]),
                    ]
                merged_bbox[2] = bboxes[j][0]
                result_tokens.extend([token, BLANK_TOKEN, tokens[j]])
                result_bboxes.extend([bbox, merged_bbox, bboxes[j]])
                i = j + 1
                continue
        result_tokens.append(token)
        result_bboxes.append(bbox)
        i += 1
    return result_tokens, result_bboxes

def run_filter_tokens(
    ocr_token_path: str,
    ocr_result_path: str,
    label_keyword_path: str,
    output_path: str
):
    token_data = load_json(ocr_token_path)
    tokens = token_data['tokens']
    bboxes = token_data['bboxes']

    ocr_raw = load_json(ocr_result_path)
    img_w = ocr_raw['images'][0]['convertedImageInfo']['width']
    img_h = ocr_raw['images'][0]['convertedImageInfo']['height']
    tables = ocr_raw['images'][0].get('tables', [])
    table_boxes = [normalize_bbox(t['boundingPoly']['vertices'], img_w, img_h) for t in tables]

    DOC_TYPE = detect_doc_type(tokens)
    if DOC_TYPE is None:
        raise ValueError("문서 유형을 감지할 수 없습니다.")
    
    with open(label_keyword_path, 'r', encoding='utf-8') as f:
        label_keywords = json.load(f)

    try:
        field_keywords = label_keywords[DOC_TYPE]["field_keywords"]
    except KeyError:
        raise ValueError(f"label_keywords.json에 '{DOC_TYPE}' 항목이 없습니다.")
    
    label_keywords = load_json(label_keyword_path)
    field_keywords = label_keywords[DOC_TYPE]["field_keywords"]
    group_keywords = label_keywords[DOC_TYPE]["group_keywords"]
    field_keywords.update(label_keywords["common"]["field_keywords"])
    group_keywords.update(label_keywords["common"]["group_keywords"])
    ALLOWED_FIELDS = set(group_keywords.keys()).union(field_keywords.keys())

    lines_by_y = group_lines_by_y_for_filter(bboxes, tolerance=10)
    blank_indices = blank_date_line_digits(tokens, bboxes, lines_by_y)

    # --- 필터링 ---
    filtered_tokens = []
    filtered_bboxes = []
    for i, (token, bbox) in enumerate(zip(tokens, bboxes)):
        if token == BLANK_TOKEN or i in blank_indices:
            filtered_tokens.append(BLANK_TOKEN)
            filtered_bboxes.append(bbox)
        elif is_in_table(bbox, table_boxes):
            filtered_tokens.append(token if token in ALLOWED_FIELDS else BLANK_TOKEN)
            filtered_bboxes.append(bbox)
        else:
            filtered_tokens.append(token)
            filtered_bboxes.append(bbox)

    # --- 후처리 ---
    date_line_y1_set = {box[1] for tok, box in zip(filtered_tokens, filtered_bboxes) if tok in {"년", "월", "일"}}
    merged_tokens, merged_bboxes = merge_inline_blanks(filtered_tokens, filtered_bboxes, date_line_y1_set)
    final_tokens, final_bboxes = inject_blank_between_colon_and_seal(merged_tokens, merged_bboxes)

    save_json(output_path, {"tokens": final_tokens, "bboxes": final_bboxes})
    print(f"✅ 문서 유형: {DOC_TYPE} → 테이블, 날짜줄, (인) 처리 완료 → {output_path}")
    return final_tokens, final_bboxes
