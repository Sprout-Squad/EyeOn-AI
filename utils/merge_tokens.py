import json
from utils.common import group_lines_by_y, save_json

def run_merge_tokens(
    table_path: str = '../data/ocr_tokens_from_table.json',
    text_path: str = '../data/ocr_tokens_from_text.json',
    output_path: str = '../data/ocr_tokens.json',
    row_tol: int = 5
):
    # --- 데이터 불러오기 ---
    with open(table_path, 'r', encoding='utf-8') as f:
        table_data = json.load(f)

    with open(text_path, 'r', encoding='utf-8') as f:
        text_data = json.load(f)

    tokens = table_data['tokens'] + text_data['tokens']
    bboxes = table_data['bboxes'] + text_data['bboxes']

    # --- y1 정규화 후 정렬 ---
    tokens_with_boxes = list(zip(tokens, bboxes))
    norm_y_map = group_lines_by_y([bbox for _, bbox in tokens_with_boxes], tolerance=row_tol)
    tokens_with_boxes.sort(key=lambda x: (norm_y_map[x[1][1]], x[1][0]))

    tokens, bboxes = zip(*tokens_with_boxes)
    merged_data = {
        "tokens": list(tokens),
        "bboxes": list(bboxes)
    }

    save_json(output_path, merged_data)
    print(f"✅ 병합 및 정렬 완료 → {output_path}")
    return list(tokens), list(bboxes)
