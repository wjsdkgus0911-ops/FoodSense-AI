"use strict";


/* =========================================================
   기본 설정
========================================================= */

const API_BASE_URL = window.location.origin;


let isAnalyzing = false;

let isSaving = false;

let pendingResult = null;


/* =========================================================
   시작
========================================================= */

console.log(
    "FoodSense AI script.js 시작"
);


/* =========================================================
   페이지 준비
========================================================= */

document.addEventListener(
    "DOMContentLoaded",
    function () {

        console.log(
            "페이지 준비 완료"
        );


        const imageInput =
            document.getElementById(
                "imageInput"
            );


        const analyzeButton =
            document.getElementById(
                "analyzeButton"
            );


        const confirmButton =
            document.getElementById(
                "confirmResultButton"
            );


        const historyButton =
            document.getElementById(
                "historyButton"
            );


        const resetDataButton =
            document.getElementById(
                "resetDataButton"
            );


        console.log(
            "imageInput =",
            imageInput
        );


        console.log(
            "analyzeButton =",
            analyzeButton
        );


        console.log(
            "confirmButton =",
            confirmButton
        );


        console.log(
            "historyButton =",
            historyButton
        );


        console.log(
            "resetDataButton =",
            resetDataButton
        );


        /* =====================================================
           이미지 선택
        ===================================================== */

        if (imageInput) {

            imageInput.addEventListener(
                "change",
                function () {

                    const file =
                        imageInput.files[0];


                    if (!file) {

                        return;

                    }


                    console.log(
                        "이미지 선택:",
                        file.name
                    );


                    const preview =
                        document.getElementById(
                            "preview"
                        );


                    if (!preview) {

                        return;

                    }


                    const reader =
                        new FileReader();


                    reader.onload =
                        function (event) {

                            preview.src =
                                event.target.result;

                            preview.style.display =
                                "block";

                        };


                    reader.readAsDataURL(
                        file
                    );

                }
            );

        }


        /* =====================================================
           분석 버튼
        ===================================================== */

        if (analyzeButton) {

            analyzeButton.addEventListener(
                "click",
                function () {

                    analyzeImage();

                }
            );

        }


        /* =====================================================
           분석 결과 저장 버튼
        ===================================================== */

        if (confirmButton) {

            confirmButton.addEventListener(
                "click",
                function () {

                    saveAnalysis();

                }
            );

        }


        /* =====================================================
           기록 새로고침
        ===================================================== */

        if (historyButton) {

            historyButton.addEventListener(
                "click",
                function () {

                    loadHistory();

                }
            );

        }


        /* =====================================================
           ★ 데이터 전체 초기화
           반드시 DOMContentLoaded 안에서 연결
        ===================================================== */

        if (resetDataButton) {

            resetDataButton.addEventListener(
                "click",
                function () {

                    resetAllData();

                }
            );

        }


        /* =====================================================
           서버 확인
        ===================================================== */

        checkServer();


        /* =====================================================
           기존 기록 불러오기
        ===================================================== */

        loadHistory();


        console.log(
            "이벤트 연결 완료"
        );

    }
);


/* =========================================================
   서버 확인
========================================================= */

async function checkServer() {

    try {

        const response =
            await fetch(
                API_URL + "/",
                {
                    method: "GET",
                    cache: "no-store"
                }
            );


        if (!response.ok) {

            throw new Error(
                "서버 상태 오류: " +
                response.status
            );

        }


        const data =
            await response.json();


        console.log(
            "FastAPI 연결 성공:",
            data
        );


        return true;


    } catch (error) {

        console.error(
            "FastAPI 연결 실패:",
            error
        );


        return false;

    }

}


/* =========================================================
   이미지 분석
========================================================= */

async function analyzeImage() {

    if (isAnalyzing) {

        return;

    }


    const imageInput =
        document.getElementById(
            "imageInput"
        );


    const analyzeButton =
        document.getElementById(
            "analyzeButton"
        );


    const confirmButton =
        document.getElementById(
            "confirmResultButton"
        );


    /* -------------------------------------------------------
       이미지 확인
    ------------------------------------------------------- */

    if (
        !imageInput ||
        !imageInput.files ||
        imageInput.files.length === 0
    ) {

        alert(
            "센서 사진을 먼저 선택해주세요."
        );

        return;

    }


    const file =
        imageInput.files[0];


    if (
        !file.type ||
        !file.type.startsWith(
            "image/"
        )
    ) {

        alert(
            "이미지 파일만 업로드할 수 있습니다."
        );

        return;

    }


    /* -------------------------------------------------------
       입력값
    ------------------------------------------------------- */

    const foodElement =
        document.getElementById(
            "foodType"
        );


    const lotElement =
        document.getElementById(
            "lotId"
        );


    const temperatureElement =
        document.getElementById(
            "temperature"
        );


    const storageDaysElement =
        document.getElementById(
            "storageDays"
        );


    const foodType =
        foodElement
            ? foodElement.value
            : "돼지고기";


    const lotId =
        lotElement
            ? lotElement.value.trim()
            : "LOT-001";


    const temperature =
        temperatureElement
            ? Number(
                temperatureElement.value
            )
            : 5;


    const storageDays =
        storageDaysElement
            ? Number(
                storageDaysElement.value
            )
            : 0;


    if (!Number.isFinite(temperature)) {

        alert(
            "보관 온도를 확인해주세요."
        );

        return;

    }


    if (!Number.isFinite(storageDays)) {

        alert(
            "보관 기간을 확인해주세요."
        );

        return;

    }


    /* -------------------------------------------------------
       FormData
    ------------------------------------------------------- */

    const formData =
        new FormData();


    formData.append(
        "file",
        file
    );


    formData.append(
        "lot_id",
        lotId || "LOT-001"
    );


    formData.append(
        "food_type",
        foodType
    );


    formData.append(
        "production_date",
        ""
    );


    formData.append(
        "temperature",
        String(
            temperature
        )
    );


    formData.append(
        "storage_days",
        String(
            storageDays
        )
    );


    /* -------------------------------------------------------
       분석 시작
    ------------------------------------------------------- */

    isAnalyzing = true;


    if (analyzeButton) {

        analyzeButton.disabled =
            true;

        analyzeButton.textContent =
            "AI 분석 중...";

    }


    if (confirmButton) {

        confirmButton.style.display =
            "none";

    }


    const waiting =
        document.getElementById(
            "analysisWaiting"
        );


    if (waiting) {

        waiting.style.display =
            "block";

        waiting.textContent =
            "센서 이미지를 분석하고 있습니다.";

    }


    try {

        console.log(
            "이미지 분석 요청"
        );


        const response =
            await fetch(
                API_URL +
                "/api/analyze-sensor",
                {
                    method: "POST",
                    body: formData
                }
            );


        const text =
            await response.text();


        let data;


        try {

            data =
                JSON.parse(text);

        } catch {

            throw new Error(
                "서버 응답이 JSON 형식이 아닙니다."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "이미지 분석에 실패했습니다."
            );

        }


        console.log(
            "분석 결과:",
            data
        );


        /* ---------------------------------------------------
           분석 결과 임시 보관
        --------------------------------------------------- */

        pendingResult =
            data;


        /* ---------------------------------------------------
           화면 출력
        --------------------------------------------------- */

        displayResult(
            data
        );


        /* ---------------------------------------------------
           저장 버튼 표시
        --------------------------------------------------- */

        if (confirmButton) {

            confirmButton.style.display =
                "block";

            confirmButton.disabled =
                false;

            confirmButton.textContent =
                "분석결과 확인하기";

        }


        if (waiting) {

            waiting.textContent =
                "분석이 완료되었습니다. 결과를 확인해주세요.";

        }


    } catch (error) {

        console.error(
            "이미지 분석 오류:",
            error
        );


        pendingResult =
            null;


        alert(
            "분석에 실패했습니다.\n\n" +
            error.message
        );


    } finally {

        isAnalyzing =
            false;


        if (analyzeButton) {

            analyzeButton.disabled =
                false;

            analyzeButton.textContent =
                "AI 분석 시작";

        }

    }

}


/* =========================================================
   분석 결과 화면
========================================================= */

function displayResult(data) {

    const waiting =
        document.getElementById(
            "analysisWaiting"
        );


    if (waiting) {

        waiting.style.display =
            "none";

    }


    /* 점수 */

    setText(
        "score",
        data.quality_score ??
        data.score
    );


    /* 상태 */

    setText(
        "qualityStatus",
        data.quality_status
    );


    /* 등급 */

    setText(
        "grade",
        data.grade ??
        data.quality_grade
    );


    /* 상태 설명 */

    setText(
        "freshness",
        data.freshness ??
        data.quality_status
    );


    /* 온도 */

    setText(
        "resultTemperature",
        data.temperature
    );


    setText(
        "resultTemperatureInfo",
        data.temperature
    );


    /* 해동 */

    setText(
        "thawCount",
        data.thaw_count
    );


    setText(
        "resultThawCount",
        data.thaw_count
    );


    /* 재동결 */

    setText(
        "refreezeCount",
        data.refreeze_count
    );


    setText(
        "resultRefreezeCount",
        data.refreeze_count
    );


    /* 온도 상태 */

    setText(
        "temperatureStatus",
        data.temperature_status
    );


    /* 식품 */

    setText(
        "resultFood",
        data.food_type
    );


    /* LOT */

    setText(
        "resultLot",
        data.lot_id
    );


    /* 보관 기간 */

    setText(
        "resultStorageDays",
        data.storage_days
    );


    /* Blue Ratio */

    const blueRatio =
        Number(
            data.blue_ratio
        );


    if (
        Number.isFinite(
            blueRatio
        )
    ) {

        setText(
            "blue",
            blueRatio.toFixed(2) +
            "%"
        );


        const bar =
            document.getElementById(
                "bar"
            );


        if (bar) {

            const width =
                Math.max(
                    0,
                    Math.min(
                        100,
                        blueRatio
                    )
                );


            bar.style.width =
                width + "%";

        }

    } else {

        setText(
            "blue",
            "-"
        );

    }


    /* 센서 영역 */

    setText(
        "sensorDetection",
        data.sensor_detection
    );


    /* RGB */

    const color =
        data.sensor_color ||
        {};


    setText(
        "r",
        color.R
    );


    setText(
        "g",
        color.G
    );


    setText(
        "b",
        color.B
    );


    /* HSV */

    const hsv =
        data.hsv ||
        {};


    setText(
        "h",
        hsv.H
    );


    setText(
        "s",
        hsv.S
    );


    setText(
        "v",
        hsv.V
    );


    /* AI 판단 */

    setText(
        "analysis",
        data.analysis ||
        (
            "품질 상태: " +
            (
                data.quality_status ||
                "-"
            )
        )
    );

}


/* =========================================================
   분석 결과 DB 저장
========================================================= */

async function saveAnalysis() {

    if (isSaving) {

        return;

    }


    if (!pendingResult) {

        alert(
            "먼저 AI 분석을 실행해주세요."
        );

        return;

    }


    const data =
        pendingResult;


    const confirmButton =
        document.getElementById(
            "confirmResultButton"
        );


    isSaving = true;


    if (confirmButton) {

        confirmButton.disabled =
            true;

        confirmButton.textContent =
            "저장 중...";

    }


    const lotElement =
        document.getElementById(
            "lotId"
        );


    const foodElement =
        document.getElementById(
            "foodType"
        );


    const temperatureElement =
        document.getElementById(
            "temperature"
        );


    const storageDaysElement =
        document.getElementById(
            "storageDays"
        );


    const lotId =
        lotElement
            ? lotElement.value.trim()
            : data.lot_id;


    const foodType =
        foodElement
            ? foodElement.value
            : data.food_type;


    const temperature =
        temperatureElement
            ? Number(
                temperatureElement.value
            )
            : Number(
                data.temperature
            );


    const storageDays =
        storageDaysElement
            ? Number(
                storageDaysElement.value
            )
            : Number(
                data.storage_days || 0
            );


    /* -------------------------------------------------------
       저장 FormData
    ------------------------------------------------------- */

    const formData =
        new FormData();


    formData.append(
        "lot_id",
        lotId || "LOT-001"
    );


    formData.append(
        "food_type",
        foodType || "돼지고기"
    );


    formData.append(
        "production_date",
        data.production_date || ""
    );


    formData.append(
        "temperature",
        String(
            temperature
        )
    );


    formData.append(
        "storage_days",
        String(
            storageDays
        )
    );


    formData.append(
        "blue_ratio",
        String(
            data.blue_ratio ?? 0
        )
    );


    formData.append(
        "quality_score",
        String(
            data.quality_score ??
            data.score ??
            0
        )
    );


    formData.append(
        "quality_grade",
        String(
            data.grade ??
            data.quality_grade ??
            "-"
        )
    );


    formData.append(
        "quality_status",
        String(
            data.quality_status ??
            "-"
        )
    );


    /* RGB */

    const color =
        data.sensor_color ||
        {};


    formData.append(
        "red",
        String(
            color.R ?? 0
        )
    );


    formData.append(
        "green",
        String(
            color.G ?? 0
        )
    );


    formData.append(
        "blue",
        String(
            color.B ?? 0
        )
    );


    /* HSV */

    const hsv =
        data.hsv ||
        {};


    formData.append(
        "hue",
        String(
            hsv.H ?? 0
        )
    );


    formData.append(
        "saturation",
        String(
            hsv.S ?? 0
        )
    );


    formData.append(
        "value",
        String(
            hsv.V ?? 0
        )
    );


    try {

        const response =
            await fetch(
                API_URL +
                "/api/save-analysis",
                {
                    method: "POST",
                    body: formData
                }
            );


        const text =
            await response.text();


        let result;


        try {

            result =
                JSON.parse(text);

        } catch {

            throw new Error(
                "저장 서버 응답이 JSON 형식이 아닙니다."
            );

        }


        if (!response.ok) {

            throw new Error(
                result.detail ||
                "DB 저장에 실패했습니다."
            );

        }


        if (!result.success) {

            throw new Error(
                "DB 저장에 실패했습니다."
            );

        }


        console.log(
            "DB 저장 성공:",
            result
        );


        /* ---------------------------------------------------
           저장 완료
        --------------------------------------------------- */

        setText(
            "analysis",
            "분석 결과가 데이터베이스에 저장되었습니다. " +
            "저장 번호: #" +
            result.saved_id
        );


        if (confirmButton) {

            confirmButton.textContent =
                "저장 완료 ✓";

            confirmButton.disabled =
                true;

        }


        /*
         * 중요:
         * pendingResult를 null로 만들지 않는다.
         * 다음 분석이 가능해야 하므로 그대로 유지한다.
         */


        /* ---------------------------------------------------
           전체 기록 다시 불러오기
        --------------------------------------------------- */

        await loadHistory();


    } catch (error) {

        console.error(
            "DB 저장 오류:",
            error
        );


        if (confirmButton) {

            confirmButton.disabled =
                false;

            confirmButton.textContent =
                "분석결과 확인하기";

        }


        alert(
            "저장에 실패했습니다.\n\n" +
            error.message
        );


    } finally {

        isSaving =
            false;

    }

}


/* =========================================================
   분석 기록 전체 조회
========================================================= */

async function loadHistory() {

    const historyMessage =
        document.getElementById(
            "historyMessage"
        );


    if (!historyMessage) {

        return;

    }


    try {

        const response =
            await fetch(
                API_URL +
                "/history?time=" +
                Date.now(),
                {
                    method: "GET",
                    cache: "no-store"
                }
            );


        const text =
            await response.text();


        let data;


        try {

            data =
                JSON.parse(text);

        } catch {

            throw new Error(
                "분석 기록 응답이 JSON 형식이 아닙니다."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "분석 기록을 불러오지 못했습니다."
            );

        }


        if (
            !data.history ||
            !Array.isArray(
                data.history
            )
        ) {

            historyMessage.innerHTML =
                "<p>저장된 분석 기록이 없습니다.</p>";

            return;

        }


        if (
            data.history.length === 0
        ) {

            historyMessage.innerHTML =
                "<p>저장된 분석 기록이 없습니다.</p>";

            return;

        }


        /* ---------------------------------------------------
           ★ DB에서 받은 전체 기록을 출력
        --------------------------------------------------- */

        let html = "";


        html += `
            <div class="history-count">
                총 ${data.history.length}건의 분석 기록
            </div>
        `;


        data.history.forEach(
            function (item) {

                html += `
                    <div class="history-item">

                        <hr>

                        <h3>
                            분석 기록 #${escapeHTML(item.id)}
                        </h3>

                        <p>
                            <strong>분석 시간:</strong>
                            ${escapeHTML(item.analyzed_at)}
                        </p>

                        <p>
                            <strong>LOT:</strong>
                            ${escapeHTML(item.lot_id)}
                        </p>

                        <p>
                            <strong>식품:</strong>
                            ${escapeHTML(item.food_type)}
                        </p>

                        <p>
                            <strong>품질 점수:</strong>
                            ${escapeHTML(item.quality_score)}
                            / 100
                        </p>

                        <p>
                            <strong>품질 등급:</strong>
                            ${escapeHTML(item.quality_grade)}
                        </p>

                        <p>
                            <strong>품질 상태:</strong>
                            ${escapeHTML(item.quality_status)}
                        </p>

                        <p>
                            <strong>현재 온도:</strong>
                            ${escapeHTML(item.temperature)}
                            ℃
                        </p>

                        <p>
                            <strong>보관 기간:</strong>
                            ${escapeHTML(item.storage_days)}
                            일
                        </p>

                        <p>
                            <strong>해동 횟수:</strong>
                            ${escapeHTML(item.thaw_count)}
                            회
                        </p>

                        <p>
                            <strong>재동결 횟수:</strong>
                            ${escapeHTML(item.refreeze_count)}
                            회
                        </p>

                        <p>
                            <strong>센서 변화율:</strong>
                            ${escapeHTML(item.blue_ratio)}
                            %
                        </p>

                    </div>
                `;

            }
        );


        historyMessage.innerHTML =
            html;


        console.log(
            "분석 기록 표시:",
            data.history.length,
            "건"
        );


    } catch (error) {

        console.error(
            "분석 기록 불러오기 실패:",
            error
        );


        historyMessage.innerHTML = `
            <p>
                기록을 불러오지 못했습니다.<br>
                ${escapeHTML(error.message)}
            </p>
        `;

    }

}


/* =========================================================
   ★ 데이터 전체 초기화
========================================================= */

async function resetAllData() {

    const resetButton =
        document.getElementById(
            "resetDataButton"
        );


    const confirmed =
        confirm(
            "⚠️ 모든 분석 데이터가 삭제됩니다.\n\n" +
            "분석 기록, 온도 기록, 해동/재동결 기록, " +
            "LOT 정보가 모두 삭제됩니다.\n\n" +
            "정말 초기화하시겠습니까?"
        );


    if (!confirmed) {

        return;

    }


    if (resetButton) {

        resetButton.disabled =
            true;

        resetButton.textContent =
            "초기화 중...";

    }


    try {

        const response =
            await fetch(
                API_URL +
                "/api/reset-data",
                {
                    method: "DELETE",
                    cache: "no-store"
                }
            );


        const text =
            await response.text();


        let data;


        try {

            data =
                JSON.parse(text);

        } catch {

            throw new Error(
                "서버 응답을 읽을 수 없습니다."
            );

        }


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "데이터 초기화에 실패했습니다."
            );

        }


        /* ---------------------------------------------------
           임시 결과 제거
        --------------------------------------------------- */

        pendingResult =
            null;


        /* ---------------------------------------------------
           결과 화면 초기화
        --------------------------------------------------- */

        setText(
            "score",
            "-"
        );

        setText(
            "qualityStatus",
            "-"
        );

        setText(
            "grade",
            "-"
        );

        setText(
            "freshness",
            "분석 대기"
        );

        setText(
            "resultTemperature",
            "-"
        );

        setText(
            "resultTemperatureInfo",
            "-"
        );

        setText(
            "thawCount",
            "-"
        );

        setText(
            "resultThawCount",
            "-"
        );

        setText(
            "refreezeCount",
            "-"
        );

        setText(
            "resultRefreezeCount",
            "-"
        );

        setText(
            "temperatureStatus",
            "-"
        );

        setText(
            "resultFood",
            "-"
        );

        setText(
            "resultLot",
            "-"
        );

        setText(
            "resultStorageDays",
            "-"
        );

        setText(
            "blue",
            "-"
        );

        setText(
            "sensorDetection",
            "-"
        );

        setText(
            "r",
            "-"
        );

        setText(
            "g",
            "-"
        );

        setText(
            "b",
            "-"
        );

        setText(
            "h",
            "-"
        );

        setText(
            "s",
            "-"
        );

        setText(
            "v",
            "-"
        );

        setText(
            "analysis",
            "분석 결과가 여기에 표시됩니다."
        );


        /* ---------------------------------------------------
           Blue Ratio bar 초기화
        --------------------------------------------------- */

        const bar =
            document.getElementById(
                "bar"
            );


        if (bar) {

            bar.style.width =
                "0%";

        }


        /* ---------------------------------------------------
           기록 화면 초기화
        --------------------------------------------------- */

        const historyMessage =
            document.getElementById(
                "historyMessage"
            );


        if (historyMessage) {

            historyMessage.innerHTML =
                "<p>저장된 분석 기록이 없습니다.</p>";

        }


        /* ---------------------------------------------------
           확인 버튼 숨김
        --------------------------------------------------- */

        const confirmButton =
            document.getElementById(
                "confirmResultButton"
            );


        if (confirmButton) {

            confirmButton.style.display =
                "none";

        }


        /* ---------------------------------------------------
           이미지 미리보기 초기화
        --------------------------------------------------- */

        const preview =
            document.getElementById(
                "preview"
            );


        if (preview) {

            preview.src =
                "";

            preview.style.display =
                "none";

        }


        const imageInput =
            document.getElementById(
                "imageInput"
            );


        if (imageInput) {

            imageInput.value =
                "";

        }


        alert(
            "데이터가 모두 초기화되었습니다."
        );


    } catch (error) {

        console.error(
            "데이터 초기화 실패:",
            error
        );


        alert(
            "데이터 초기화에 실패했습니다.\n\n" +
            error.message
        );


    } finally {

        if (resetButton) {

            resetButton.disabled =
                false;

            resetButton.textContent =
                "데이터 전체 초기화";

        }

    }

}


/* =========================================================
   텍스트 출력
========================================================= */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (!element) {

        console.warn(
            "HTML 요소 없음:",
            id
        );

        return;

    }


    if (
        value === undefined ||
        value === null ||
        value === ""
    ) {

        element.textContent =
            "-";

    } else {

        element.textContent =
            String(value);

    }

}


/* =========================================================
   HTML 안전 처리
========================================================= */

function escapeHTML(value) {

    return String(
        value ?? ""
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );

}


/* =========================================================
   전역 등록
========================================================= */

window.analyzeImage =
    analyzeImage;


window.displayResult =
    displayResult;


window.saveAnalysis =
    saveAnalysis;


window.loadHistory =
    loadHistory;


window.resetAllData =
    resetAllData;


console.log(
    "FoodSense AI script.js 등록 완료"
);
