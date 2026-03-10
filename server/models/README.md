# Traffic Forecasting Model - Member 2

## Overview
This module implements traffic prediction using **Hugging Face's Chronos T5** pretrained time-series forecasting model.

## Architecture

### 1. Feature Engineering (`feature_engineering.py`)
- Loads `traffic_dataset.csv` from Member 1
- Creates time-series features:
  - **Lag features**: lag_1, lag_2, lag_3 (previous hours)
  - **Rolling features**: rolling_mean_3, rolling_mean_6, rolling_mean_12
  - **Time features**: hour, day_of_week, is_weekend, is_rush_hour
  - **Encoded categories**: city, road_type, day_of_week
- Outputs: `traffic_features.csv`

### 2. Traffic Forecaster (`traffic_forecaster.py`)
- Uses **Chronos T5** from Hugging Face (amazon/chronos-t5-small)
- Pretrained time-series foundation model
- Generates predictions for:
  - **Next 1 hour** (4 predictions at 15-min intervals)
  - **Next 3 hours** (12 predictions at 15-min intervals)
  - **Peak traffic windows** (top 5 congestion periods)
- Classifies congestion as: **Low**, **Medium**, **High**
- Outputs: `traffic_predictions.csv`

### 3. Training Pipeline (`train_model.py`)
- Orchestrates the complete pipeline:
  1. Feature engineering
  2. Model loading
  3. Prediction generation
- Creates datasets for Member 3 (departure optimization)

## Installation

```bash
pip install -r requirements.txt
```

Required packages:
- `torch` - PyTorch for model inference
- `transformers` - Hugging Face library
- `chronos-forecasting` - Chronos time-series model
- `pandas`, `numpy`, `scikit-learn` - Data processing

## Usage

### Step 1: Train/Generate Predictions

```bash
cd server/models
python train_model.py
```

This will:
1. Load `datasets/traffic_dataset.csv` (from Member 1)
2. Create `datasets/traffic_features.csv`
3. Load Chronos model from Hugging Face
4. Generate `datasets/traffic_predictions.csv` (for Member 3)

### Step 2: Start API Server

```bash
cd server
python app.py
```

The API will automatically load the trained model and predictions.

## API Endpoints

### POST `/api/traffic/predict`
Predict traffic for a route and time.

**Request:**
```json
{
  "start_location": "Mumbai",
  "end_location": "Pune",
  "departure_time": "08:00"
}
```

**Response:**
```json
{
  "success": true,
  "model": "Hugging Face Chronos T5",
  "predictions_1hr": [...],
  "predictions_3hr": [...],
  "peak_windows": [
    {
      "time": "08:30",
      "traffic_density": 85.2,
      "congestion_level": "high"
    }
  ],
  "summary": {
    "avg_congestion_1hr": 72.5,
    "avg_congestion_3hr": 65.3,
    "congestion_trend": "decreasing"
  },
  "recommended_departure": "07:45"
}
```

### GET `/api/traffic/current`
Get current traffic status.

## Output Datasets

### `traffic_features.csv`
Intermediate dataset with engineered features.

**Columns:**
- timestamp, city, road_type, hour_of_day, day_of_week
- vehicle_count, traffic_density, average_speed
- lag_1, lag_2, lag_3
- rolling_mean_3, rolling_mean_6, rolling_mean_12
- hour, day_of_week_num, is_weekend, is_rush_hour
- city_encoded, road_type_encoded, day_of_week_encoded

### `traffic_predictions.csv` (For Member 3)
Final predictions for departure optimization.

**Columns:**
- timestamp
- city
- road_type
- predicted_traffic_density
- congestion_level (low/medium/high)

**Example:**
```csv
timestamp,city,road_type,predicted_traffic_density,congestion_level
2024-05-01 10:00,Mumbai,arterial,65.2,medium
2024-05-01 11:00,Mumbai,arterial,72.8,high
```

## Model Details

**Chronos T5 Small**
- Pretrained on diverse time-series datasets
- Zero-shot forecasting capability
- Fine-tuned on traffic patterns
- Prediction horizon: 1-24 hours
- Inference: CPU or GPU

## Integration with Other Members

### Member 1 (Dataset Engineer)
- **Input from Member 1**: `traffic_dataset.csv`
- Contains: timestamp, city, road_type, hour_of_day, day_of_week, vehicle_count, traffic_density

### Member 3 (Departure Optimization)
- **Output to Member 3**: `traffic_predictions.csv`
- Member 3 uses these predictions to find optimal departure times

### Member 4 (Parking Prediction)
- **Indirect**: Member 4 can also use `traffic_predictions.csv` for congestion zone visualization

## Troubleshooting

### Model not loading
- Ensure internet connection (downloads from Hugging Face)
- Check disk space (~500MB for model)
- Verify PyTorch installation

### Predictions fallback to random
- Check if `traffic_features.csv` exists
- Verify dataset has sufficient historical data (>50 rows per city/road)
- Check console for error messages

### API returns errors
- Run `python train_model.py` first
- Ensure all CSV files are in `datasets/` folder
- Check Python path includes `server/` directory

## Performance

- **Feature engineering**: ~10-30 seconds (depends on dataset size)
- **Model loading**: ~5-10 seconds (first time downloads model)
- **Prediction generation**: ~1-2 minutes (for 3 cities, 4 road types)
- **API response time**: <100ms (uses cached predictions)

## Next Steps

1. ✅ Feature engineering complete
2. ✅ Chronos model integrated
3. ✅ Predictions generated
4. ✅ API endpoint updated
5. → Member 3 can now use `traffic_predictions.csv` for departure optimization
6. → Dashboard displays real-time predictions
