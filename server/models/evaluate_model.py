import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, mean_squared_error

base_path = Path(__file__).parent.parent.parent
sys.path.append(str(base_path / "server"))

from models.traffic_forecaster import TrafficForecaster


def mean_absolute_percentage_error(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    non_zero_mask = y_true != 0
    if not np.any(non_zero_mask):
        return 0.0
    return float(np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100)


def evaluate_model(holdout_points=24):
    features_path = base_path / "datasets" / "traffic_features.csv"
    df = pd.read_csv(features_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    forecaster = TrafficForecaster()
    forecaster.load_model()

    y_true = []
    y_pred = []
    labels_true = []
    labels_pred = []
    evaluated_series = []

    grouped = df.groupby(["city", "road_type"], sort=True)
    for (city, road_type), group in grouped:
        series = group.sort_values("timestamp").reset_index(drop=True)
        if len(series) <= holdout_points + 100:
            continue

        train_series = series.iloc[:-holdout_points]
        test_series = series.iloc[-holdout_points:]

        predictions = forecaster.predict_future(
            train_series["traffic_density"].to_numpy(),
            prediction_length=holdout_points
        )

        predictions = np.array(predictions[:holdout_points], dtype=float)
        actual = test_series["traffic_density"].to_numpy(dtype=float)

        y_true.extend(actual.tolist())
        y_pred.extend(predictions.tolist())
        labels_true.extend(test_series["congestion_level"].tolist())
        labels_pred.extend([forecaster.classify_congestion(value) for value in predictions])
        evaluated_series.append(
            {
                "city": city,
                "road_type": road_type,
                "points": holdout_points
            }
        )

    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred) ** 0.5
    mape = mean_absolute_percentage_error(y_true, y_pred)
    accuracy = accuracy_score(labels_true, labels_pred)
    macro_f1 = f1_score(labels_true, labels_pred, average="macro")

    results = {
        "model": "amazon/chronos-t5-small",
        "evaluation_method": "Time-based holdout using the last 24 hourly points from each city-road_type series",
        "evaluated_series": len(evaluated_series),
        "forecast_points": len(y_true),
        "metrics": {
            "mae": round(float(mae), 4),
            "rmse": round(float(rmse), 4),
            "mape": round(float(mape), 4),
            "accuracy": round(float(accuracy), 4),
            "macro_f1": round(float(macro_f1), 4)
        },
        "series_breakdown": evaluated_series
    }

    return results


def main():
    results = evaluate_model()
    output_path = base_path / "server" / "models" / "evaluation_results.json"
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print(json.dumps(results, indent=2))
    print(f"\nSaved evaluation results to: {output_path}")


if __name__ == "__main__":
    main()
