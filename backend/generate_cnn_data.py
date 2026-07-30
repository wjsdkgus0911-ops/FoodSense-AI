import os
import cv2
import numpy as np


# ==========================================
# 설정
# ==========================================

DATASET_DIR = "dataset"

IMAGE_SIZE = 224

# 등급별 생성할 이미지 수
IMAGES_PER_CLASS = 50


CLASSES = {
    "A+": 0,
    "A": 1,
    "B+": 2,
    "B": 3,
    "C": 4,
    "D": 5
}


# ==========================================
# 폴더 생성
# ==========================================

for grade in CLASSES:

    folder = os.path.join(
        DATASET_DIR,
        grade
    )

    os.makedirs(
        folder,
        exist_ok=True
    )


# ==========================================
# 가상 센서 이미지 생성 함수
# ==========================================

def create_sensor_image(
    blue_level
):

    img = np.zeros(
        (
            IMAGE_SIZE,
            IMAGE_SIZE,
            3
        ),
        dtype=np.uint8
    )


    # --------------------------------------
    # 배경 생성
    # --------------------------------------

    background = np.random.normal(
        235,
        5,
        (
            IMAGE_SIZE,
            IMAGE_SIZE,
            3
        )
    )


    background = np.clip(
        background,
        0,
        255
    )


    img = background.astype(
        np.uint8
    )


    # --------------------------------------
    # 중앙 센서 위치
    # --------------------------------------

    center_x = IMAGE_SIZE // 2
    center_y = IMAGE_SIZE // 2

    radius = 55


    # 센서 기본색
    # OpenCV는 BGR 순서

    white = np.array(
        [235, 235, 235],
        dtype=np.float32
    )

    blue = np.array(
        [170, 70, 70],
        dtype=np.float32
    )


    # --------------------------------------
    # 흰색 → 파란색 변화
    # --------------------------------------

    sensor_color = (

        white * (1 - blue_level)
        +
        blue * blue_level

    )


    sensor_color = np.clip(
        sensor_color,
        0,
        255
    ).astype(
        np.uint8
    )


    # --------------------------------------
    # 센서 원형 영역
    # --------------------------------------

    cv2.circle(
        img,
        (
            center_x,
            center_y
        ),
        radius,
        tuple(
            int(x)
            for x in sensor_color
        ),
        -1
    )


    # --------------------------------------
    # 센서 내부 색상 변화
    # --------------------------------------

    for _ in range(25):

        x = np.random.randint(
            center_x - radius + 5,
            center_x + radius - 5
        )

        y = np.random.randint(
            center_y - radius + 5,
            center_y + radius - 5
        )


        if (
            (x-center_x)**2
            +
            (y-center_y)**2
            <
            (radius-5)**2
        ):

            noise = np.random.randint(
                -12,
                13
            )


            color = np.clip(
                sensor_color.astype(
                    np.int16
                )
                +
                noise,
                0,
                255
            )


            cv2.circle(
                img,
                (x, y),
                np.random.randint(
                    2,
                    7
                ),
                tuple(
                    int(v)
                    for v in color
                ),
                -1
            )


    # --------------------------------------
    # 센서 외곽선
    # --------------------------------------

    cv2.circle(
        img,
        (
            center_x,
            center_y
        ),
        radius,
        (190, 190, 190),
        2
    )


    # --------------------------------------
    # 약간의 사진 노이즈
    # --------------------------------------

    noise = np.random.normal(
        0,
        3,
        img.shape
    )


    img = img.astype(
        np.float32
    ) + noise


    img = np.clip(
        img,
        0,
        255
    ).astype(
        np.uint8
    )


    # --------------------------------------
    # 약간의 밝기 변화
    # --------------------------------------

    brightness = np.random.uniform(
        0.9,
        1.1
    )


    img = np.clip(
        img.astype(
            np.float32
        ) * brightness,
        0,
        255
    ).astype(
        np.uint8
    )


    return img


# ==========================================
# 등급별 가상 데이터 생성
# ==========================================

blue_levels = {

    "A+": (0.00, 0.08),

    "A": (0.08, 0.20),

    "B+": (0.20, 0.40),

    "B": (0.40, 0.60),

    "C": (0.60, 0.82),

    "D": (0.82, 1.00)

}


print()
print("==============================")
print("가상 CNN 데이터 생성")
print("==============================")
print()


for grade in CLASSES:

    folder = os.path.join(
        DATASET_DIR,
        grade
    )


    low, high = blue_levels[
        grade
    ]


    for i in range(
        IMAGES_PER_CLASS
    ):

        blue_level = np.random.uniform(
            low,
            high
        )


        image = create_sensor_image(
            blue_level
        )


        filename = (
            f"synthetic_"
            f"{grade}_"
            f"{i:03d}.jpg"
        )


        save_path = os.path.join(
            folder,
            filename
        )


        cv2.imwrite(
            save_path,
            image
        )


    print(
        f"{grade}: "
        f"{IMAGES_PER_CLASS}장 생성 완료"
    )


print()
print("==============================")
print("가상 데이터 생성 완료")
print("==============================")
print()
print(
    "dataset 폴더를 확인하세요."
)
