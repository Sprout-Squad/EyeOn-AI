import json
import re
from collections import defaultdict
from utils.common import (
    normalize_bbox,
    remove_spaces_from_tokens,
    save_json
)

# 설정
KEYWORD_SPLIT = [":", "(인)", "(서명)"]
SPECIAL_SPLIT_TOKENS = ["□"]
BLANK_TOKEN = "[BLANK]"
FIXED_BLANK_WIDTH = {"년": 60, "월": 25, "일": 25}
SPECIAL_BLANK_WIDTH = 25
ROW_TOL = 15

def split_number_dot_text(text):
    match = re.match(r"^(\d+\.)\s*(.*)$", text)
    return [match.group(1), match.group(2)] if match else None

def split_special_tokens(text):
    parts = []
    buffer = ""
    for ch in text:
        if ch in SPECIAL_SPLIT_TOKENS:
            if buffer:
                parts.append(buffer)
                buffer = ""
            parts.append(BLANK_TOKEN)
        else:
            buffer += ch
    if buffer:
        parts.append(buffer)
    return parts

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

def run_text_token_extraction(input_path='../data/ocr_result.json', output_path='../data/ocr_tokens_from_text.json'):
    with open(input_path, 'r', encoding='utf-8') as f:
        ocr_data = json.load(f)

    image_info = ocr_data['images'][0]
    fields = image_info['fields']
    img_width = image_info['convertedImageInfo']['width']
    img_height = image_info['convertedImageInfo']['height']
    tables = image_info.get('tables', [])
    table_bboxes = [normalize_bbox(table['boundingPoly']['vertices'], img_width, img_height) for table in tables]

    def is_inside_table(bbox):
        x0, y0, x1, y1 = bbox
        return any(x0 >= tb[0] and y0 >= tb[1] and x1 <= tb[2] and y1 <= tb[3] for tb in table_bboxes)

    def is_number_dot_only(text):
        return bool(re.match(r'^\d+\.$', text.strip()))

    tokens, bboxes = [], []

    for field in fields:
        text = field['inferText']
        bbox = normalize_bbox(field['boundingPoly']['vertices'], img_width, img_height)

        if is_inside_table(bbox) or is_number_dot_only(text):
            continue

        split_parts = split_number_dot_text(text) or [text]

        more_split_parts = []
        for part in split_parts:
            pattern = "(" + "|".join(re.escape(k) for k in KEYWORD_SPLIT) + ")"
            more_split_parts.extend([p for p in re.split(pattern, part) if p])

        final_parts = []
        for part in more_split_parts:
            final_parts.extend(split_special_tokens(part))

        total_width = bbox[2] - bbox[0]
        remaining_parts = [p for p in final_parts if p != BLANK_TOKEN]
        remaining_width = total_width - SPECIAL_BLANK_WIDTH * final_parts.count(BLANK_TOKEN)
        total_len = sum(len(p) for p in remaining_parts)

        px = bbox[0]
        for part in final_parts:
            if part == BLANK_TOKEN:
                w = SPECIAL_BLANK_WIDTH
            else:
                w = int(len(part) / total_len * remaining_width) if total_len else remaining_width
            part_bbox = [px, bbox[1], px + w, bbox[3]]
            tokens.append(part)
            bboxes.append(part_bbox)
            px += w

    # 정렬
    tokens = remove_spaces_from_tokens(tokens)
    norm_y_map = group_lines_by_y(bboxes, tolerance=ROW_TOL)
    tokens_with_boxes = sorted(zip(tokens, bboxes), key=lambda x: (norm_y_map[x[1][1]], x[1][0]))
    tokens, bboxes = zip(*tokens_with_boxes)
    tokens = list(tokens)
    bboxes = list(bboxes)

    # ":" 다음에 [BLANK] 삽입
    new_tokens = []
    new_bboxes = []
    for i in range(len(tokens) - 1):
        curr_token = tokens[i]
        next_token = tokens[i + 1]
        curr_box = bboxes[i]
        next_box = bboxes[i + 1]

        new_tokens.append(curr_token)
        new_bboxes.append(curr_box)

        # ":" 다음에 [BLANK] 삽입
        if curr_token == ":":
            # (인)이 뒤쪽에 있는지 검사
            j = i + 1
            found_in = False
            while j < len(tokens):
                if tokens[j] == "(인)":
                    found_in = True
                    break
                elif tokens[j] != BLANK_TOKEN:
                    # : 와 (인) 사이에 글자가 있음
                    found_in = False
                    break
                j += 1
        
            if found_in:
                # 삽입 조건 충족
                if abs(curr_box[1] - next_box[1]) <= ROW_TOL:
                    blank_box = [curr_box[2], min(curr_box[1], next_box[1]), next_box[0], max(curr_box[3], next_box[3])]
                else:
                    blank_box = [curr_box[2], curr_box[1], curr_box[2] + 500, curr_box[3]]
                new_tokens.append(BLANK_TOKEN)
                new_bboxes.append(blank_box)
        
        # "년", "월", "일" 앞에도 [BLANK] 삽입
        if next_token in FIXED_BLANK_WIDTH and len(next_token.strip()) == 1:
            # ➕ 앞 토큰이 숫자면 BLANK 삽입하지 않음
            if curr_token.isdigit():
                continue
            
            # 같은 줄이면 ":"처럼 사이에 넣고, 아니면 왼쪽에 고정폭 삽입
            if abs(curr_box[1] - next_box[1]) <= ROW_TOL:
                blank_box = [curr_box[2], min(curr_box[1], next_box[1]), next_box[0], max(curr_box[3], next_box[3])]
            else:
                w = FIXED_BLANK_WIDTH[next_token]
                blank_box = [next_box[0] - w, next_box[1], next_box[0], next_box[3]]
        
            new_tokens.append(BLANK_TOKEN)
            new_bboxes.append(blank_box)
        

    # 마지막 토큰 추가
    new_tokens.append(tokens[-1])
    new_bboxes.append(bboxes[-1])

    # 저장
    save_json(output_path, {"tokens": new_tokens, "bboxes": new_bboxes})
    print(f"✅ 텍스트 토큰 추출 완료: {output_path}")
    