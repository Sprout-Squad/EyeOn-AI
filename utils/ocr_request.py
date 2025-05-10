import os
import uuid
import time
import json
import requests
from dotenv import load_dotenv
from utils.common import save_json

# --- 환경 변수 로드 ---
load_dotenv()
secret_key = os.getenv("CLOVA_OCR_SECRET")
url = os.getenv("CLOVA_OCR_URL")

if not secret_key or not url:
    raise EnvironmentError(".env에서 CLOVA_OCR_SECRET 또는 CLOVA_OCR_URL을 불러오지 못했습니다.")

# --- OCR 호출 및 결과 파일 저장 ---
def call_clova_ocr(base64_string: str, file_ext: str = "jpg") -> str:
    if not base64_string:
        raise ValueError("이미지 데이터가 비어 있습니다.")
    if file_ext.lower() not in {"jpg", "jpeg", "png"}:
        raise ValueError(f"지원하지 않는 확장자입니다: {file_ext}")

    payload = {
        "version": "V2",
        "requestId": str(uuid.uuid4()),
        "timestamp": int(time.time() * 1000),
        "lang": "ko",
        "images": [
            {
                "format": file_ext,
                "name": f"doc.{file_ext}",
                "data": base64_string
            }
        ],
        "enableTableDetection": True
    }

    headers = {
        "Content-Type": "application/json",
        "X-OCR-SECRET": secret_key
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()

    result = response.json()
    filename = "ocr_result.json"

    save_json(filename, result)
    print(f"✅ OCR 결과 저장 완료 → {filename}")
    return filename
