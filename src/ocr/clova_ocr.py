import requests
import base64
import json
import time

# 이미지 파일을 base64로 인코딩
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# 요청 보낼 URL, 헤더, 바디 설정
url = "https://fg1gf0xxhu.apigw.ntruss.com/custom/v1/40550/ebabb5a4d9df26cf40dba7fc180c4e319f41289a5ebedfd14a25ed0f2fc6ac64/general"

headers = {
    "Content-Type": "application/json",
    "X-OCR-SECRET": "eHFScml5VXROZkFVTXdYZ2xvZmpQYnBod01NWnJqeGE="
}

# 이미지 base64 인코딩
# 아직은 백엔드 서버로부터 이미지 인코딩 값을 받는 게 아니기 때문에 번거롭더라도 파일명을 계속 변경해서 사용해주세요.
image_path = "../data/train/images/resume_01.png"
image_data = encode_image_to_base64(image_path)

# JSON 본문 구성
payload = {
    "version": "V2",
    "requestId": "auto-test-001",
    "timestamp": int(time.time() * 1000),
    "images": [
        {
            "name": "doc.png",
            "format": "png",
            "data": image_data
        }
    ],
    "enableTableDetection": True
}

# POST 요청
response = requests.post(url, headers=headers, data=json.dumps(payload))

if response.status_code == 200:
    result = response.json()
    
    # 결과 파일 저장
    save_path = "../data/train/annotations/ocr_result.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"OCR 결과가 {save_path}에 저장되었습니다.")
else:
    print(f"Error {response.status_code}: {response.text}")