// ==========================================
// FoodSense AI - TensorFlow.js CNN
// ==========================================

let cnnModel = null;

const CNN_CLASSES = ["A+", "A", "B+", "B", "C", "D"];


// ==========================================
// 가상 센서 데이터 생성
// ==========================================

function createSyntheticData() {

    const xs = [];
    const ys = [];

    const samplesPerClass = 80;

    CNN_CLASSES.forEach((grade, classIndex) => {

        for (let i = 0; i < samplesPerClass; i++) {

            // 클래스별 파란색 변화 정도
            const blueLevel = getBlueLevel(
                classIndex
            );

            // 16 x 16 x 3 RGB 데이터
            const image = [];

            for (let y = 0; y < 16; y++) {

                for (let x = 0; x < 16; x++) {

                    const distance = Math.sqrt(
                        Math.pow(x - 7.5, 2) +
                        Math.pow(y - 7.5, 2)
                    );

                    // 중앙 원형 센서
                    if (distance < 6.5) {

                        const noise =
                            (Math.random() - 0.5) * 0.08;

                        const white = 0.92;
                        const blue = 0.65;

                        const value =
                            blueLevel * blue +
                            (1 - blueLevel) * white +
                            noise;

                        // RGB
                        image.push(
                            value * 0.35, // R
                            value * 0.45, // G
                            value        // B
                        );

                    } else {

                        // 배경
                        const background =
                            0.88 +
                            (Math.random() - 0.5) * 0.05;

                        image.push(
                            background,
                            background,
                            background
                        );
                    }
                }
            }

            xs.push(image);

            const label = Array(
                CNN_CLASSES.length
            ).fill(0);

            label[classIndex] = 1;

            ys.push(label);
        }
    });

    return {
        xs,
        ys
    };
}


// ==========================================
// 등급별 파란색 변화
// ==========================================

function getBlueLevel(classIndex) {

    const ranges = [

        [0.00, 0.05], // A+
        [0.05, 0.20], // A
        [0.20, 0.40], // B+
        [0.40, 0.60], // B
        [0.60, 0.82], // C
        [0.82, 1.00]  // D

    ];

    const [min, max] =
        ranges[classIndex];

    return (
        min +
        Math.random() * (max - min)
    );
}


// ==========================================
// CNN 모델 생성
// ==========================================

function createCNNModel() {

    const model =
        tf.sequential();

    model.add(
        tf.layers.conv2d({

            inputShape: [
                16,
                16,
                3
            ],

            filters: 16,

            kernelSize: 3,

            activation: "relu"

        })
    );

    model.add(
        tf.layers.maxPooling2d({

            poolSize: 2,

            strides: 2

        })
    );

    model.add(
        tf.layers.conv2d({

            filters: 32,

            kernelSize: 3,

            activation: "relu"

        })
    );

    model.add(
        tf.layers.maxPooling2d({

            poolSize: 2,

            strides: 2

        })
    );

    model.add(
        tf.layers.flatten()
    );

    model.add(
        tf.layers.dense({

            units: 64,

            activation: "relu"

        })
    );

    model.add(
        tf.layers.dropout({

            rate: 0.3

        })
    );

    model.add(
        tf.layers.dense({

            units: 6,

            activation: "softmax"

        })
    );


    model.compile({

        optimizer: tf.train.adam(0.001),

        loss: "categoricalCrossentropy",

        metrics: ["accuracy"]

    });


    return model;
}


// ==========================================
// CNN 학습
// ==========================================

async function trainCNN() {

    console.log(
        "FoodSense AI CNN 학습 시작"
    );


    if (typeof tf === "undefined") {

        console.error(
            "TensorFlow.js가 로드되지 않았습니다."
        );

        return;

    }


    const data =
        createSyntheticData();


    const xs = tf.tensor4d(
    data.xs.flat(),
    [
        data.xs.length,
        16,
        16,
        3
    ]
);


    const ys = tf.tensor2d(
        data.ys,
        [
            data.ys.length,
            6
        ]
    );


    cnnModel =
        createCNNModel();


    console.log(
        "CNN 모델 생성 완료"
    );


    await cnnModel.fit(
        xs,
        ys,
        {

            epochs: 15,

            batchSize: 32,

            shuffle: true,

            callbacks: {

                onEpochEnd:
                    (epoch, logs) => {

                        console.log(

                            `Epoch ${
                                epoch + 1
                            }/15`,

                            "accuracy:",
                            logs.acc ??
                            logs.accuracy

                        );

                    }

            }

        }
    );


    xs.dispose();
    ys.dispose();


    console.log(
        "CNN 학습 완료!"
    );


    return cnnModel;
}


// ==========================================
// CNN 테스트
// ==========================================

async function predictWithCNN(
    blueRatio
) {

    if (!cnnModel) {

        console.log(
            "CNN 모델을 먼저 학습합니다."
        );

        await trainCNN();

    }


    // Blue Ratio를 가상의 센서 이미지로 변환
    const blueLevel =
        Math.min(
            1,
            Math.max(
                0,
                blueRatio / 100
            )
        );


    const image = [];


    for (let y = 0; y < 16; y++) {

        for (let x = 0; x < 16; x++) {

            const distance = Math.sqrt(
                Math.pow(x - 7.5, 2) +
                Math.pow(y - 7.5, 2)
            );


            if (distance < 6.5) {

                const white = 0.92;
                const blue = 0.65;

                const value =
                    blueLevel * blue +
                    (1 - blueLevel) * white;


                image.push(
                    value * 0.35,
                    value * 0.45,
                    value
                );

            } else {

                image.push(
                    0.88,
                    0.88,
                    0.88
                );

            }
        }
    }


    const input = tf.tensor4d(
        image,
        [
            1,
            16,
            16,
            3
        ]
    );


    const prediction =
        cnnModel.predict(input);


    const probabilities =
        await prediction.data();


    input.dispose();
    prediction.dispose();


    let maxIndex = 0;


    for (
        let i = 1;
        i < probabilities.length;
        i++
    ) {

        if (
            probabilities[i]
            >
            probabilities[maxIndex]
        ) {

            maxIndex = i;

        }

    }


    return {

        grade:
            CNN_CLASSES[maxIndex],

        confidence:
            Math.round(
                probabilities[maxIndex] * 100
            ),

        probabilities:
            probabilities.map(
                value =>
                    Math.round(
                        value * 100
                    )
            )

    };
}


// ==========================================
// 테스트용 함수
// ==========================================

window.trainFoodSenseCNN =
    trainCNN;

window.predictFoodSenseCNN =
    predictWithCNN;
    window.addEventListener("load", async () => {

    console.log("FoodSense AI 시작");

    try {

        await trainCNN();

        console.log(
            "CNN 준비 완료"
        );

    } catch (error) {

        console.error(
            "CNN 학습 오류:",
            error
        );

    }

});
