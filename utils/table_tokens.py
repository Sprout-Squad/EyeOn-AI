import json
from utils.common import (
    normalize_bbox,
    remove_number_dot_prefix,
    remove_spaces_from_tokens,
    save_json
)

ignore_tokens = {"만원", "만세", "=", "-", "점", "급", "cm", "kg"}
BLANK_TOKEN = "[BLANK]"

def run_table_token_extraction(input_path='../data/ocr_result.json', output_path='../data/ocr_tokens_from_table.json'):
    with open(input_path, 'r', encoding='utf-8') as f:
        ocr_data = json.load(f)

    img_width = ocr_data['images'][0]['convertedImageInfo']['width']
    img_height = ocr_data['images'][0]['convertedImageInfo']['height']
    tables = ocr_data['images'][0].get('tables', [])

    tokens, bboxes = [], []

    for table in tables:
        for cell in table.get('cells', []):
            bbox = normalize_bbox(cell['boundingPoly']['vertices'], img_width, img_height)
            cell_text_lines = cell.get('cellTextLines', [])

            text = ''
            if not cell_text_lines or all('cellWords' not in line or not line['cellWords'] for line in cell_text_lines):
                text = BLANK_TOKEN
            else:
                for line in cell_text_lines:
                    if 'cellWords' in line:
                        text += ''.join(word['inferText'] for word in line['cellWords'])
                text = text.strip()
                if text in ignore_tokens or text == '':
                    text = BLANK_TOKEN

            tokens.append(text)
            bboxes.append(bbox)

    tokens = remove_spaces_from_tokens(tokens)

    save_json(output_path, {"tokens": tokens, "bboxes": bboxes})
    print(f"✅ 테이블 토큰 추출 완료 → {output_path}")
