from flask import request, jsonify
import os, time
import json
from . import api_blueprint
from utils.ocr_request import call_clova_ocr
from utils.table_tokens import run_table_token_extraction
from utils.text_tokens import run_text_token_extraction
from utils.merge_tokens import run_merge_tokens
from utils.filter_tokens import run_filter_tokens
from utils.response_util import success, error
from utils.layoutlm_inference import run_layoutlm_inference

# 프로젝트 루트 경로 기준 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

@api_blueprint.route("/api/ai/modify", methods=["POST"])
def predict_modify():
    try:
        data = request.get_json()

        base64_image = data.get("image_base64")
        file_ext = data.get("file_ext", "jpg").lower()

        # 1. OCR 요청 및 결과 저장
        ocr_filename = call_clova_ocr(base64_image, file_ext)
        ocr_path = os.path.join(DATA_DIR, ocr_filename)

        # OCR 결과 파일 생성될 때까지 대기
        for _ in range(10):
            if os.path.exists(ocr_path):
                break
            time.sleep(0.5)
        else:
            raise FileNotFoundError(f"OCR 결과 파일이 생성되지 않았습니다: {ocr_path}")

        # 2. 테이블 토큰 추출
        run_table_token_extraction(
            input_path=ocr_path,
            output_path=os.path.join(DATA_DIR, 'ocr_tokens_from_table.json')
        )

        # 3. 텍스트 토큰 추출
        run_text_token_extraction(
            input_path=ocr_path,
            output_path=os.path.join(DATA_DIR, 'ocr_tokens_from_text.json')
        )

        # 4. 병합
        merged_path = os.path.join(DATA_DIR, 'ocr_tokens.json')
        run_merge_tokens(
            table_path=os.path.join(DATA_DIR, 'ocr_tokens_from_table.json'),
            text_path=os.path.join(DATA_DIR, 'ocr_tokens_from_text.json'),
            output_path=merged_path
        )

        # 5. 수정용 필터링 처리
        run_filter_tokens(
            ocr_token_path=merged_path,
            ocr_result_path=ocr_path,
            label_keyword_path=os.path.join(DATA_DIR, 'label_keywords.json'),
            output_path=os.path.join(DATA_DIR, 'ocr_tokens_filtered.json')
        )

        # 6. LayoutLM 추론
        with open(os.path.join(DATA_DIR, 'ocr_tokens_filtered.json'), 'r', encoding='utf-8') as f:
            filtered = json.load(f)
        result = run_layoutlm_inference(filtered['tokens'], filtered['bboxes'])

        # 7. ocr_tokens.json 병합 결과도 함께 읽기
        with open(merged_path, 'r', encoding='utf-8') as f:
            merged_tokens = json.load(f)

        # 8. 성공 응답 반환
        return success(
            message="수정용 분석 성공",
            code=200,
            filename="ocr_tokens_filtered.json",
            base64_str=None,
            result={
                "layoutlm_result": result,
                "merged_tokens": merged_tokens
            })
    
    except ValueError as ve:
        return error(str(ve), code=400)

    except Exception as e:
        return error(str(e), code=500)
