import cv2
import base64
import numpy as np

# Step 1: Edge Detection
def detect_edges(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blurred, 50, 150)
    return edged

# Step 2: Contour Detection
def find_document_contour(edged_image):
    contours, _ = cv2.findContours(edged_image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    for contour in contours:
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

        if len(approx) == 4:
            return approx

    raise Exception("문서 윤곽선(사각형)을 찾을 수 없습니다.")

# Step 3: Perspective Correction
def order_points(pts):
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]  # top-left
    rect[2] = pts[np.argmax(s)]  # bottom-right
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left
    return rect

def apply_perspective_transform(image, pts):
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    widthA = np.linalg.norm(br - bl)
    widthB = np.linalg.norm(tr - tl)
    maxWidth = max(int(widthA), int(widthB))

    heightA = np.linalg.norm(tr - br)
    heightB = np.linalg.norm(tl - bl)
    maxHeight = max(int(heightA), int(heightB))

    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight), flags=cv2.INTER_LINEAR)

    return warped

# Step 4: Image Enhancement (스캔 스타일 + 글자/테두리 강화)
def enhance_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # ✅ 노이즈 제거 추가
    gray = cv2.fastNlMeansDenoising(gray, None, h=15, templateWindowSize=7, searchWindowSize=21)


    # CLAHE로 대비 향상
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # 강한 sharpening
    sharpen_kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, sharpen_kernel)

    # 강한 adaptive threshold
    binary = cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        25, 7
    )


    # 미세한 팽창으로 테두리/글자 강화
    kernel = np.ones((2, 2), np.uint8)
    final = cv2.dilate(binary, kernel, iterations=1)

    return final

# Step 5: 여백 추가
def add_padding(image, padding=40, color=(255, 255, 255)):
    return cv2.copyMakeBorder(
        image,
        top=padding,
        bottom=padding,
        left=padding,
        right=padding,
        borderType=cv2.BORDER_CONSTANT,
        value=color
    )

def add_outer_padding(image, padding=40):
    color = [255, 255, 255]  # 흰 배경
    return cv2.copyMakeBorder(image, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=color)

# Step 6: Deskew 정확 보정 (Hough Transform 기반)
def deskew_image(image):
    import cv2
    import numpy as np

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)

    if lines is None:
        print("[경고] Hough Line 없음. Deskew 생략")
        return image

    angles = []
    for rho, theta in lines[:, 0]:
        angle_deg = (theta * 180 / np.pi) - 90

        # ✅ 수평 기준 ±15도 이내 직선만 선택
        if -15 < angle_deg < 15:
            angles.append(angle_deg)

    if not angles:
        print("[경고] 적절한 수평 라인 없음. Deskew 생략")
        return image

    median_angle = np.median(angles)

    if abs(median_angle) > 10:
        print(f"[경고] 회전 각도 {median_angle:.2f}도 -> Deskew 생략")
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    print(f"[✔️ Deskew 완료] {median_angle:.2f}도 회전 적용")
    return rotated


# 전체 처리 흐름
def scan_document(image):
    if image is None:
        raise ValueError("이미지를 불러올 수 없습니다.")

    image = add_outer_padding(image, padding=50)
    edged = detect_edges(image)
    doc_cnt = find_document_contour(edged)
    warped = apply_perspective_transform(image, doc_cnt.reshape(4, 2))
    final = enhance_image(warped)
    deskewed = deskew_image(final)
    padded = add_padding(deskewed, padding=40)

    _, buffer = cv2.imencode('.png', padded)
    encoded_string = base64.b64encode(buffer).decode('utf-8')
    return encoded_string