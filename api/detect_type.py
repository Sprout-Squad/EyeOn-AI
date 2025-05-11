from flask import request, jsonify
import os, time
import json
from . import api_blueprint
from utils.ocr_request import call_clova_ocr
from utils.response_util import success, error
from utils.common import remove_spaces_from_tokens
from utils.common import detect_doc_type

# 프로젝트 루트 경로 기준 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

@api_blueprint.route("/api/ai/detect", methods=["POST"])
def detect_document_type():
    try:
        data = request.get_json()
        base64_image = data.get("image_base64")
        file_ext = data.get("file_ext", "jpg").lower()

        if not base64_image:
            return error("image_base64가 누락되었습니다.", code=400)

        # OCR 수행
        ocr_filename = call_clova_ocr(base64_image, file_ext)
        ocr_path = os.path.join(DATA_DIR, ocr_filename)

        for _ in range(10):
            if os.path.exists(ocr_path):
                break
            time.sleep(0.5)
        else:
            raise FileNotFoundError(f"OCR 결과 파일이 생성되지 않았습니다: {ocr_path}")

        # 토큰 추출 후 문서 타입 감지
        with open(ocr_path, 'r', encoding='utf-8') as f:
            ocr_result = json.load(f)

        tokens = [field["inferText"] for field in ocr_result["images"][0].get("fields", [])]
        tokens = remove_spaces_from_tokens(tokens)
        doc_type = detect_doc_type(tokens)

        if doc_type:
            return success(
                message="문서 타입 감지 성공",
                code=200,
                doc_type = doc_type
            )
    except ValueError as ve:
        return error(str(ve), code=400)

    except Exception as e:
        return error(str(e), code=500)
