import cv2
import numpy as np
import os
import shutil
from datetime import datetime


# =========================================================
# 센서 분석
# =========================================================

def analyze_sensor(image_path):

    img = cv2.imread(image_path)

    if img is None:
        return {
            "error": "이미지를 읽을 수 없습니다."
        }

    original = img.copy()

    height, width = img.shape[:2]

    # =====================================================
    # 1. 사진 중앙 영역만 분석
    # =====================================================

    # 외곽의 배경이나 다른 물체가 센서로 검출되는 것을 방지
    margin_x = int(width * 0.20)
    margin_y = int(height * 0.20)

    center_area = img[
        margin_y:height - margin_y,
        margin_x:width - margin_x
    ]

    center_h, center_w = center_area.shape[:2]

    center_x = center_w // 2
    center_y = center_h // 2


    # =====================================================
    # 2. 중앙 영역에서 센서 후보 찾기
    # =====================================================

    hsv_center = cv2.cvtColor(
        center_area,
        cv2.COLOR_BGR2HSV
    )

    gray_center = cv2.cvtColor(
        center_area,
        cv2.COLOR_BGR2GRAY
    )

    gray_center = cv2.GaussianBlur(
        gray_center,
        (5, 5),
        0
    )


    # -----------------------------------------------------
    # 중앙에서 색 변화가 있는 영역을 찾기
    # -----------------------------------------------------

    # 파란색 검출
    blue_mask = cv2.inRange(
        hsv_center,
        np.array([90, 25, 30]),
        np.array([140, 255, 255])
    )


    # 노이즈 제거
    kernel = np.ones(
        (5, 5),
        np.uint8
    )

    blue_mask = cv2.morphologyEx(
        blue_mask,
        cv2.MORPH_OPEN,
        kernel
    )

    blue_mask = cv2.morphologyEx(
        blue_mask,
        cv2.MORPH_CLOSE,
        kernel
    )


    contours, _ = cv2.findContours(
        blue_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )


    candidate = None


    # =====================================================
    # 3. 중앙에서 검출된 파란 영역 중
    #    중앙에 가까운 영역 선택
    # =====================================================

    if len(contours) > 0:

        best_score = -999999


        for contour in contours:

            area = cv2.contourArea(contour)

            if area < 100:
                continue


            x, y, w, h = cv2.boundingRect(
                contour
            )


            contour_center_x = x + w // 2
            contour_center_y = y + h // 2


            distance = np.sqrt(
                (contour_center_x - center_x) ** 2
                +
                (contour_center_y - center_y) ** 2
            )


            # 중앙에 가까울수록 높은 점수
            center_score = -distance


            # 너무 작은 영역은 제외
            area_score = min(area / 1000, 100)


            score = (
                center_score
                +
                area_score
            )


            if score > best_score:

                best_score = score

                candidate = (
                    x,
                    y,
                    w,
                    h
                )


    # =====================================================
    # 4. 센서 영역 결정
    # =====================================================

    if candidate is not None:

        x, y, w, h = candidate


        # 너무 작은 검출 영역이면 중앙 고정 영역 사용
        if w < center_w * 0.08 or h < center_h * 0.08:

            candidate = None


    # =====================================================
    # 5. 검출 실패 시 중앙 센서 영역 사용
    # =====================================================

    if candidate is None:

        # 센서가 중앙에 있다는 조건을 이용한 안전한 fallback
        roi_size = int(
            min(width, height) * 0.22
        )


        cx = width // 2
        cy = height // 2


        x1 = max(
            0,
            cx - roi_size
        )

        y1 = max(
            0,
            cy - roi_size
        )

        x2 = min(
            width,
            cx + roi_size
        )

        y2 = min(
            height,
            cy + roi_size
        )


        roi = img[
            y1:y2,
            x1:x2
        ]


        # 중앙 영역 표시
        cv2.rectangle(
            original,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            4
        )


        detection = (
            "센서 자동 검출 실패 → "
            "중앙 센서 영역을 분석했습니다."
        )


    else:

        x, y, w, h = candidate


        # 중앙 영역 좌표를 전체 사진 좌표로 변환
        x1 = x + margin_x
        y1 = y + margin_y

        x2 = x1 + w
        y2 = y1 + h


        # 센서 주변을 조금 확장
        padding = int(
            max(w, h) * 0.15
        )


        x1 = max(
            0,
            x1 - padding
        )

        y1 = max(
            0,
            y1 - padding
        )

        x2 = min(
            width,
            x2 + padding
        )

        y2 = min(
            height,
            y2 + padding
        )


        roi = img[
            y1:y2,
            x1:x2
        ]


        # 검출된 센서 영역 표시
        cv2.rectangle(
            original,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            4
        )


        detection = (
            "중앙 영역에서 "
            "센서 후보를 자동 검출했습니다."
        )


    # =====================================================
    # 6. 분석 폴더 생성
    # =====================================================

    os.makedirs(
        "analyzed",
        exist_ok=True
    )


    cv2.imwrite(
        "analyzed/detection.jpg",
        original
    )


    cv2.imwrite(
        "analyzed/roi.jpg",
        roi
    )


    # =====================================================
    # 7. RGB 분석
    # =====================================================

    rgb = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2RGB
    )


    R, G, B = cv2.mean(rgb)[:3]


    # =====================================================
    # 8. HSV 분석
    # =====================================================

    hsv = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2HSV
    )


    H, S, V = cv2.mean(hsv)[:3]


    # =====================================================
    # 9. Blue Ratio
    # =====================================================

    blue_mask_roi = cv2.inRange(
        hsv,
        np.array([90, 50, 40]),
        np.array([140, 255, 255])
    )


    blue_ratio = (
        np.sum(blue_mask_roi > 0)
        /
        blue_mask_roi.size
    ) * 100


    blue_ratio = min(
        100,
        max(
            0,
            blue_ratio
        )
    )


    # =====================================================
    # 10. 등급 판정
    # =====================================================

    if blue_ratio < 10:

        grade = "A+"
        state = "초기 상태"


    elif blue_ratio < 25:

        grade = "A"
        state = "신선"


    elif blue_ratio < 45:

        grade = "B+"
        state = "변화 감지"


    elif blue_ratio < 65:

        grade = "B"
        state = "품질 저하"


    elif blue_ratio < 85:

        grade = "C"
        state = "부패 진행"


    else:

        grade = "D"
        state = "섭취 주의"


    score = max(
        0,
        round(100 - blue_ratio)
    )


    # =====================================================
    # 11. 결과 반환
    # =====================================================

    return {

        "grade": grade,

        "score": score,

        "freshness": state,

        "sensor_detection": detection,

        "sensor_color": {

            "R": round(R),

            "G": round(G),

            "B": round(B)

        },

        "hsv": {

            "H": round(H),

            "S": round(S),

            "V": round(V)

        },

        "blue_ratio": round(
            blue_ratio,
            2
        ),

        "analysis": (
            f"{detection} "
            f"센서의 청색화 정도는 "
            f"{blue_ratio:.2f}%입니다."
        )

    }


# =========================================================
# CNN 학습용 데이터 저장
# =========================================================

def save_dataset(
    image_path,
    grade
):

    folder = os.path.join(
        "dataset",
        grade
    )


    os.makedirs(
        folder,
        exist_ok=True
    )


    filename = (
        datetime.now()
        .strftime("%Y%m%d_%H%M%S_%f")
        + ".jpg"
    )


    save_path = os.path.join(
        folder,
        filename
    )


    shutil.copy(
        image_path,
        save_path
    )


    return save_path
