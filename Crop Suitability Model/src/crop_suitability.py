import joblib
import pandas as pd

model = joblib.load("Crop Suitability Model/Models/crop_suitability_pipeline.pkl")


def predict_crop(N, P, K, temperature, humidity, ph, rainfall):

    data = pd.DataFrame([[
        N, P, K, temperature, humidity, ph, rainfall
    ]], columns=[
        "N", "P", "K", "temperature",
        "humidity", "ph", "rainfall"
    ])

    return model.predict(data)[0]


if __name__ == "__main__":
    result = predict_crop(
        90, 42, 43, 20.9, 82, 6.5, 202
    )

    print("Predicted Crop:", result)