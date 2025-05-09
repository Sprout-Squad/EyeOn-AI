import cv2
import numpy as np
from flask import request
from api import api_blueprint
from utils.scanner import scan_document
from utils.response_util import success, error

@api_blueprint.route('/api/ai/scan', methods=['POST'])
def scan_ai_document():
    file = request.files.get('file')
    if not file:
        return error("이미지 파일이 없습니다.", 400)

    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    if image is None:
        return error("이미지를 디코딩할 수 없습니다.", 400)

    try:
        base64_result = scan_document(image)
        return success("스캔 완료", 200, filename=file.filename, base64_str=base64_result)
    except Exception as e:
        return error(str(e), 500)
