"""
FoodSense AI
바이오센서 기반 식품 품질 분석 플랫폼

실행:
    uvicorn app:app --reload
"""

import os
import sqlite3
from datetime import datetime

import cv2
import numpy as np

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    Request
)

from pathlib import Path

from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


# ============================================================
# 1. FastAPI
# ============================================================

app = FastAPI(
    title="FoodSense AI",
    version="4.0.1"
)


# ============================================================
# 2. Frontend 경로
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# 3. Templates
# ============================================================

templates = Jinja2Templates(
    directory=str(FRONTEND_DIR)
)


# ============================================================
# 4. Static 파일
# ============================================================

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static"
)

# ============================================================
# 2. Blue Ratio 등급 기준
# ============================================================

BLUE_THRESHOLDS = [
    (0.5, "A+"),
    (1.5, "A"),
    (3.0, "B+"),
    (5.0, "B"),
    (7.0, "C+"),
    (10.0, "C"),
]


def calculate_grade(
    blue_ratio: float
):

    blue_ratio = max(
        0.0,
        min(
            100.0,
            float(blue_ratio)
        )
    )

    if blue_ratio < 0.5:
        return "A+", "정상"

    elif blue_ratio < 1.5:
        return "A", "정상"

    elif blue_ratio < 3.0:
        return "B+", "정상"

    elif blue_ratio < 5.0:
        return "B", "주의"

    elif blue_ratio < 7.0:
        return "C+", "주의"

    elif blue_ratio < 10.0:
        return "C", "위험"

    else:
        return "D", "위험"
    
# ============================================================
# 3. DB 연결
# ============================================================

def get_db():

    conn = sqlite3.connect(
        DB_PATH,
        timeout=10
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# 4. DB 초기화
# ============================================================

def init_database():

    conn = get_db()

    try:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS products_lot (

                lot_id TEXT PRIMARY KEY,

                product_name TEXT NOT NULL,

                production_date TEXT,

                created_at TEXT NOT NULL

            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_analysis (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                lot_id TEXT NOT NULL,

                image_url TEXT,

                food_type TEXT,

                rgb_r REAL,

                rgb_g REAL,

                rgb_b REAL,

                hsv_h REAL,

                hsv_s REAL,

                hsv_v REAL,

                blue_ratio REAL,

                quality_score REAL,

                quality_grade TEXT,

                quality_status TEXT,

                temperature REAL,

                storage_days REAL DEFAULT 0,

                thaw_count INTEGER DEFAULT 0,

                refreeze_count INTEGER DEFAULT 0,

                created_at TEXT NOT NULL

            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS temperature_logs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                lot_id TEXT NOT NULL,

                temperature REAL NOT NULL,

                status TEXT NOT NULL,

                timestamp TEXT NOT NULL

            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS thaw_history (

                lot_id TEXT PRIMARY KEY,

                thaw_count INTEGER NOT NULL DEFAULT 0,

                refreeze_count INTEGER NOT NULL DEFAULT 0

            )
            """
        )

        conn.commit()

        ensure_column(
            conn,
            "sensor_analysis",
            "storage_days",
            "REAL DEFAULT 0"
        )

        ensure_column(
            conn,
            "sensor_analysis",
            "thaw_count",
            "INTEGER DEFAULT 0"
        )

        ensure_column(
            conn,
            "sensor_analysis",
            "refreeze_count",
            "INTEGER DEFAULT 0"
        )

        conn.commit()

        print("=" * 60)
        print("FoodSense AI DB 초기화 완료")
        print("DB 위치:", DB_PATH)
        print("=" * 60)

    finally:

        conn.close()


# ============================================================
# 5. 기존 DB 컬럼 보정
# ============================================================

def ensure_column(
    conn,
    table_name,
    column_name,
    column_definition
):

    columns = conn.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    existing_columns = [
        row["name"]
        for row in columns
    ]

    if column_name not in existing_columns:

        conn.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_definition}
            """
        )

        print(
            f"DB 컬럼 추가: "
            f"{table_name}.{column_name}"
        )


# ============================================================
# 6. DB 시작
# ============================================================

init_database()


# ============================================================
# 7. 기본 페이지
# ============================================================

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

# ============================================================
# 8. 온도 상태
# ============================================================

def get_temperature_status(
    temperature: float
):

    temperature = float(temperature)

    if temperature <= 0:
        return "냉동"

    if temperature <= 10:
        return "냉장"

    if temperature <= 25:
        return "상온"

    return "고온"


# ============================================================
# 9. 센서 ROI
# ============================================================

def detect_sensor_roi(
    image
):

    if image is None:
        raise ValueError(
            "이미지가 없습니다."
        )

    height, width = image.shape[:2]

    if height < 20 or width < 20:
        raise ValueError(
            "이미지 크기가 너무 작습니다."
        )

    x1 = int(width * 0.25)
    x2 = int(width * 0.75)

    y1 = int(height * 0.25)
    y2 = int(height * 0.75)

    roi = image[
        y1:y2,
        x1:x2
    ]

    if roi.size == 0:
        raise ValueError(
            "센서 영역을 검출하지 못했습니다."
        )

    return (
        roi,
        x1,
        y1,
        x2,
        y2
    )


# ============================================================
# 10. RGB / HSV / Blue Ratio
# ============================================================

def analyze_sensor_color(
    roi
):

    if roi is None or roi.size == 0:
        raise ValueError(
            "센서 ROI가 비어 있습니다."
        )

    if len(roi.shape) != 3 or roi.shape[2] != 3:
        raise ValueError(
            "올바른 컬러 이미지가 아닙니다."
        )

    # --------------------------------------------------------
    # BGR 평균
    # --------------------------------------------------------

    bgr_mean = np.mean(
        roi.reshape(-1, 3),
        axis=0
    )

    b_value = float(
        bgr_mean[0]
    )

    g_value = float(
        bgr_mean[1]
    )

    r_value = float(
        bgr_mean[2]
    )

    # --------------------------------------------------------
    # HSV
    # --------------------------------------------------------

    hsv_image = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2HSV
    )

    hsv_mean = np.mean(
        hsv_image.reshape(-1, 3),
        axis=0
    )

    h_value = float(
        hsv_mean[0]
    )

    s_value = float(
        hsv_mean[1]
    )

    v_value = float(
        hsv_mean[2]
    )

    # --------------------------------------------------------
    # Blue Ratio
    # --------------------------------------------------------

    pixels = roi.reshape(
        -1,
        3
    ).astype(
        np.float32
    )

    B = pixels[:, 0]
    G = pixels[:, 1]
    R = pixels[:, 2]

    blue_mask = (
        (B > R * 1.05) &
        (B > G * 1.05) &
        (B > 80)
    )

    blue_ratio = (
        float(
            np.mean(
                blue_mask
            )
        )
        * 100
    )

    return {

        "R": round(
            r_value,
            2
        ),

        "G": round(
            g_value,
            2
        ),

        "B": round(
            b_value,
            2
        ),

        "H": round(
            h_value,
            2
        ),

        "S": round(
            s_value,
            2
        ),

        "V": round(
            v_value,
            2
        ),

        "blue_ratio": round(
            blue_ratio,
            2
        )

    }


# ============================================================
# 11. 품질 점수
# ============================================================

def calculate_quality(
    blue_ratio: float,
    temperature: float
):

    blue_ratio = max(
        0.0,
        min(
            100.0,
            float(blue_ratio)
        )
    )

    temperature = float(
        temperature
    )

    # --------------------------------------------------------
    # 품질 점수
    # 청색 변화가 증가할수록 점수가 감소
    # 너무 급격하게 감소하지 않도록 완화
    # --------------------------------------------------------

    score = 100.0 - (
        blue_ratio * 0.5
    )

    # --------------------------------------------------------
    # 온도 보정
    # --------------------------------------------------------

    if temperature > 10:

        score -= min(
            10,
            (temperature - 10) * 0.8
        )

    if temperature > 25:

        score -= 5

    # --------------------------------------------------------
    # 점수 범위 제한
    # --------------------------------------------------------

    score = max(
        0.0,
        min(
            100.0,
            score
        )
    )

    # --------------------------------------------------------
    # 등급은 점수가 아니라
    # 실제 Blue Ratio 기준으로 판정
    # --------------------------------------------------------

    grade, status = calculate_grade(
        blue_ratio
    )

    return (
        round(score, 2),
        grade,
        status
    )

# ============================================================
# 12. 해동 / 재동결
# ============================================================

def get_thaw_info(
    conn,
    lot_id
):

    row = conn.execute(
        """
        SELECT
            thaw_count,
            refreeze_count
        FROM thaw_history
        WHERE lot_id = ?
        """,
        (lot_id,)
    ).fetchone()

    if row:

        return (
            int(row["thaw_count"]),
            int(row["refreeze_count"])
        )

    return (
        0,
        0
    )


# ============================================================
# 13. 이미지 분석
# ============================================================

@app.post(
    "/api/analyze-sensor"
)
async def analyze_sensor(

    file: UploadFile = File(...),

    lot_id: str = Form("LOT-001"),

    food_type: str = Form("돼지고기"),

    production_date: str = Form(""),

    temperature: float = Form(5),

    storage_days: float = Form(0)

):

    if not file.content_type:

        raise HTTPException(
            status_code=400,
            detail="파일 형식을 확인할 수 없습니다."
        )

    if not file.content_type.startswith(
        "image/"
    ):

        raise HTTPException(
            status_code=400,
            detail="이미지 파일만 업로드할 수 있습니다."
        )

    image_bytes = await file.read()

    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="이미지가 비어 있습니다."
        )

    image_array = np.frombuffer(
        image_bytes,
        dtype=np.uint8
    )

    image = cv2.imdecode(
        image_array,
        cv2.IMREAD_COLOR
    )

    if image is None:

        raise HTTPException(
            status_code=400,
            detail="이미지를 읽을 수 없습니다."
        )

    try:

        # ----------------------------------------------------
        # ROI
        # ----------------------------------------------------

        roi, x1, y1, x2, y2 = (
            detect_sensor_roi(
                image
            )
        )

        # ----------------------------------------------------
        # 색상 분석
        # ----------------------------------------------------

        color_data = (
            analyze_sensor_color(
                roi
            )
        )

        # ----------------------------------------------------
        # 품질 계산
        # ----------------------------------------------------

        score, grade, status = (
            calculate_quality(
                color_data["blue_ratio"],
                temperature
            )
        )

        temperature_status = (
            get_temperature_status(
                temperature
            )
        )

        # ----------------------------------------------------
        # LOT 정보
        # ----------------------------------------------------

        conn = get_db()

        try:

            thaw_count, refreeze_count = (
                get_thaw_info(
                    conn,
                    lot_id
                )
            )

        finally:

            conn.close()

        # ----------------------------------------------------
        # 이미지 저장
        # ----------------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        filename = (
            f"{lot_id}_"
            f"{timestamp}.jpg"
        )

        filepath = os.path.join(
            UPLOAD_DIR,
            filename
        )

        cv2.imwrite(
            filepath,
            image
        )

        # ----------------------------------------------------
        # AI 판단 문장
        # ----------------------------------------------------

        if grade in ["A+", "A"]:

            analysis_text = (
                "바이오센서의 청색 변화가 낮은 수준으로 "
                "확인되어 현재 품질 상태가 정상 범위로 "
                "판단됩니다."
            )

        elif grade in ["B+", "B"]:

            analysis_text = (
                "바이오센서에서 청색 변화가 일부 확인되어 "
                "품질 변화가 진행되고 있을 가능성이 있습니다."
            )

        elif grade in ["C+", "C"]:

            analysis_text = (
                "바이오센서의 색상 변화가 비교적 크게 "
                "확인되어 품질 상태를 주의 깊게 확인해야 합니다."
            )

        else:

            analysis_text = (
                "바이오센서의 색상 변화가 크게 확인되어 "
                "품질 저하 가능성이 높은 상태로 판단됩니다."
            )

        return {

            "success": True,

            "lot_id":
                lot_id,

            "food_type":
                food_type,

            "production_date":
                production_date,

            "temperature":
                temperature,

            "storage_days":
                storage_days,

            "temperature_status":
                temperature_status,

            "thaw_count":
                thaw_count,

            "refreeze_count":
                refreeze_count,

            "sensor_detection":
                "중앙 영역에서 바이오센서 후보 ROI를 자동 검출했습니다.",

            "roi": {

                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2

            },

            # 내부 분석용 데이터
            "sensor_color": {

                "R":
                    color_data["R"],

                "G":
                    color_data["G"],

                "B":
                    color_data["B"]

            },

            "hsv": {

                "H":
                    color_data["H"],

                "S":
                    color_data["S"],

                "V":
                    color_data["V"]

            },

            "blue_ratio":
                color_data["blue_ratio"],

            "quality_score":
                score,

            "score":
                score,

            "grade":
                grade,

            "quality_grade":
                grade,

            "quality_status":
                status,

            "freshness":
                status,

            "analysis":
                analysis_text

        }

    except Exception as error:

        print(
            "이미지 분석 오류:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "이미지 분석 중 오류가 발생했습니다: "
                + str(error)
            )
        )


# ============================================================
# 14. 분석 결과 저장
# ============================================================

@app.post(
    "/api/save-analysis"
)
async def save_analysis(

    lot_id: str = Form("LOT-001"),

    food_type: str = Form("돼지고기"),

    production_date: str = Form(""),

    temperature: float = Form(5),

    storage_days: float = Form(0),

    blue_ratio: float = Form(0),

    quality_score: float = Form(0),

    quality_grade: str = Form("-"),

    quality_status: str = Form("-"),

    red: float = Form(0),

    green: float = Form(0),

    blue: float = Form(0),

    hue: float = Form(0),

    saturation: float = Form(0),

    value: float = Form(0)

):

    conn = get_db()

    try:

        conn.execute(
            """
            INSERT OR IGNORE INTO products_lot
            (
                lot_id,
                product_name,
                production_date,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                lot_id,
                food_type,
                production_date,
                datetime.now().isoformat()
            )
        )

        thaw_count, refreeze_count = (
            get_thaw_info(
                conn,
                lot_id
            )
        )

        cursor = conn.execute(
            """
            INSERT INTO sensor_analysis
            (
                lot_id,
                image_url,
                food_type,
                rgb_r,
                rgb_g,
                rgb_b,
                hsv_h,
                hsv_s,
                hsv_v,
                blue_ratio,
                quality_score,
                quality_grade,
                quality_status,
                temperature,
                storage_days,
                thaw_count,
                refreeze_count,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lot_id,
                "",
                food_type,
                red,
                green,
                blue,
                hue,
                saturation,
                value,
                blue_ratio,
                quality_score,
                quality_grade,
                quality_status,
                temperature,
                storage_days,
                thaw_count,
                refreeze_count,
                datetime.now().isoformat()
            )
        )

        saved_id = cursor.lastrowid

        temperature_status = (
            get_temperature_status(
                temperature
            )
        )

        conn.execute(
            """
            INSERT INTO temperature_logs
            (
                lot_id,
                temperature,
                status,
                timestamp
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                lot_id,
                temperature,
                temperature_status,
                datetime.now().isoformat()
            )
        )

        conn.commit()

        return {

            "success": True,

            "saved_id":
                saved_id,

            "lot_id":
                lot_id,

            "food_type":
                food_type,

            "temperature":
                temperature,

            "storage_days":
                storage_days,

            "thaw_count":
                thaw_count,

            "refreeze_count":
                refreeze_count,

            "quality_score":
                quality_score,

            "quality_grade":
                quality_grade,

            "quality_status":
                quality_status,

            "blue_ratio":
                blue_ratio

        }

    except Exception as error:

        conn.rollback()

        print(
            "DB 저장 오류:",
            repr(error)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "DB 저장 중 오류가 발생했습니다: "
                + str(error)
            )
        )

    finally:

        conn.close()


# ============================================================
# 15. 분석 기록 조회
# ============================================================

@app.get(
    "/history"
)
def get_history():

    conn = get_db()

    try:

        rows = conn.execute(
            """
            SELECT
                id,
                lot_id,
                food_type,
                quality_score,
                quality_grade,
                quality_status,
                temperature,
                storage_days,
                thaw_count,
                refreeze_count,
                blue_ratio,
                created_at
            FROM sensor_analysis
            ORDER BY id DESC
            """
        ).fetchall()

        history = []

        for row in rows:

            history.append({

                "id":
                    row["id"],

                "lot_id":
                    row["lot_id"],

                "food_type":
                    row["food_type"],

                "quality_score":
                    row["quality_score"],

                "quality_grade":
                    row["quality_grade"],

                "quality_status":
                    row["quality_status"],

                "temperature":
                    row["temperature"],

                "storage_days":
                    row["storage_days"],

                "thaw_count":
                    row["thaw_count"],

                "refreeze_count":
                    row["refreeze_count"],

                "blue_ratio":
                    row["blue_ratio"],

                "analyzed_at":
                    row["created_at"]

            })

        return {

            "success": True,

            "history":
                history

        }

    finally:

        conn.close()


# ============================================================
# 16. 온도 로그
# ============================================================

@app.post(
    "/api/temperature-log"
)
def save_temperature_log(

    lot_id: str = Form(...),

    temperature: float = Form(...)

):

    conn = get_db()

    try:

        status = (
            get_temperature_status(
                temperature
            )
        )

        conn.execute(
            """
            INSERT INTO temperature_logs
            (
                lot_id,
                temperature,
                status,
                timestamp
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                lot_id,
                temperature,
                status,
                datetime.now().isoformat()
            )
        )

        conn.commit()

        return {

            "success": True,

            "lot_id":
                lot_id,

            "temperature":
                temperature,

            "status":
                status

        }

    finally:

        conn.close()


# ============================================================
# 17. 해동 / 재동결
# ============================================================

@app.post(
    "/api/update-thaw"
)
def update_thaw(

    lot_id: str = Form(...),

    thaw_count: int = Form(0),

    refreeze_count: int = Form(0)

):

    thaw_count = max(
        0,
        thaw_count
    )

    refreeze_count = max(
        0,
        refreeze_count
    )

    conn = get_db()

    try:

        conn.execute(
            """
            INSERT INTO thaw_history
            (
                lot_id,
                thaw_count,
                refreeze_count
            )
            VALUES (?, ?, ?)

            ON CONFLICT(lot_id)
            DO UPDATE SET
                thaw_count = excluded.thaw_count,
                refreeze_count = excluded.refreeze_count
            """,
            (
                lot_id,
                thaw_count,
                refreeze_count
            )
        )

        conn.commit()

        return {

            "success": True,

            "lot_id":
                lot_id,

            "thaw_count":
                thaw_count,

            "refreeze_count":
                refreeze_count

        }

    finally:

        conn.close()


# ============================================================
# 18. 전체 초기화
# ============================================================

@app.delete(
    "/api/reset-data"
)
def reset_data():

    conn = get_db()

    try:

        conn.execute(
            "DELETE FROM sensor_analysis"
        )

        conn.execute(
            "DELETE FROM temperature_logs"
        )

        conn.execute(
            "DELETE FROM thaw_history"
        )

        conn.execute(
            "DELETE FROM products_lot"
        )

        conn.execute(
            """
            DELETE FROM sqlite_sequence
            WHERE name IN (
                'sensor_analysis',
                'temperature_logs'
            )
            """
        )

        conn.commit()

        return {

            "success": True,

            "message":
                "모든 FoodSense AI 데이터가 초기화되었습니다."

        }

    except Exception as error:

        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "데이터 초기화 중 오류가 발생했습니다: "
                + str(error)
            )
        )

    finally:

        conn.close()


# ============================================================
# 19. LOT별 기록
# ============================================================

@app.get(
    "/api/history/{lot_id}"
)
def get_lot_history(
    lot_id: str
):

    conn = get_db()

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM sensor_analysis
            WHERE lot_id = ?
            ORDER BY id DESC
            """,
            (lot_id,)
        ).fetchall()

        result = []

        for row in rows:

            result.append(
                dict(row)
            )

        return {

            "success": True,

            "lot_id":
                lot_id,

            "count":
                len(result),

            "history":
                result

        }

    finally:

        conn.close()
