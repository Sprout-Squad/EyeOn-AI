from flask import request, jsonify
import os, time
from . import api_blueprint
from utils.ocr_request import call_clova_ocr
from utils.table_tokens import run_table_token_extraction
from utils.text_tokens import run_text_token_extraction
from utils.merge_tokens import run_merge_tokens
from utils.response_util import success, error

# 프로젝트 루트 경로 기준 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

@api_blueprint.route("/api/ai/create", methods=["POST"])
def predict_create():
    try:
        data = request.get_json()

        # base64 인코딩된 이미지와 확장자 받아오기
        base64_image = data.get("image_base64")
        file_ext = data.get("file_ext", "jpg").lower()

        if not base64_image:
            return jsonify({"error": "image_base64 필드가 비어 있습니다."}), 400

        # 1. OCR 요청 및 결과 저장
        ocr_filename = call_clova_ocr(base64_image, file_ext)
        ocr_path = os.path.join(DATA_DIR, ocr_filename)

        # ✅ OCR 결과 파일 생성될 때까지 기다림 (최대 5초)
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
        tokens, bboxes = run_merge_tokens(
            table_path=os.path.join(DATA_DIR, 'ocr_tokens_from_table.json'),
            text_path=os.path.join(DATA_DIR, 'ocr_tokens_from_text.json'),
            output_path=os.path.join(DATA_DIR, 'ocr_tokens.json')
        )

        # 5. LayoutLM 추론 (TODO)
        # result = run_layoutlm_inference(tokens, bboxes)

        # 6. LayoutLM 추론 결과 대신 현재는 토큰과 박스만 반환
        return success("분석 성공", code=200, filename=ocr_filename, base64_str=None)

    except Exception as e:
        return error(f"예외 발생: {str(e)}", code=500)
