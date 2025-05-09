from flask import request, jsonify
import os, time
from . import api_blueprint
from utils.ocr_request import call_clova_ocr
from utils.table_tokens import run_table_token_extraction
from utils.text_tokens import run_text_token_extraction
from utils.merge_tokens import run_merge_tokens
from utils.filter_tokens import run_filter_tokens
from utils.response_util import success, error

# 프로젝트 루트 경로 기준 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

@api_blueprint.route("/api/ai/modify", methods=["POST"])
def predict_modify():
    try:
        data = request.get_json()

        base64_image = data.get("image_base64")
        file_ext = data.get("file_ext", "jpg").lower()

        if not base64_image:
            return jsonify({"error": "image_base64 필드가 비어 있습니다."}), 400

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
        run_merge_tokens(
            table_path=os.path.join(DATA_DIR, 'ocr_tokens_from_table.json'),
            text_path=os.path.join(DATA_DIR, 'ocr_tokens_from_text.json'),
            output_path=os.path.join(DATA_DIR, 'ocr_tokens.json')
        )

        # 5. 수정용 필터링 처리
        run_filter_tokens(
            ocr_token_path=os.path.join(DATA_DIR, 'ocr_tokens.json'),
            ocr_result_path=ocr_path,
            label_keyword_path=os.path.join(DATA_DIR, 'label_keywords.json'),
            output_path=os.path.join(DATA_DIR, 'ocr_tokens_filtered.json')
        )

        # 6. LayoutLM 추론 (TODO)

        # 7. 필터링된 결과 기준으로 성공 반환
        return success("수정용 분석 성공", code=200, filename="ocr_tokens_filtered.json", base64_str=None)

    except Exception as e:
        return error(f"예외 발생: {str(e)}", code=500)
