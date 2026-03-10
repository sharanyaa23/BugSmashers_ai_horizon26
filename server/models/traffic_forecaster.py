import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import joblib
from sklearn.preprocessing import StandardScaler

# Try to import heavy ML dependencies, but allow graceful fallback if missing
try:
    import torch
    from chronos import ChronosPipeline
    _HAS_CHRONOS = True
except Exception as e:  # pragma: no cover - dev environment without Chronos/torch
    torch = None
    ChronosPipeline = None
    _HAS_CHRONOS = False
    print(f"Warning: Chronos / torch not available, using rule-based traffic predictions. Details: {e}")

class TrafficForecaster:
    def __init__(self, model_name="amazon/chronos-t5-small"):
        self.model_name = model_name
        self.pipeline = None
        self.scaler = StandardScaler()
        # If torch is not available, we will never load the Chronos model
        if torch is not None and hasattr(torch, "cuda"):
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = "cpu"
        
    def load_model(self):
        if not _HAS_CHRONOS:
            # In lightweight environments we skip loading the heavy model.
            # The rest of the app will fall back to rule-based traffic predictions.
            raise RuntimeError("Chronos / torch not installed; cannot load ML model.")

        print(f"Loading Chronos model: {self.model_name} on {self.device}...")
        self.pipeline = ChronosPipeline.from_pretrained(
            self.model_name,
            device_map=self.device,
            torch_dtype=torch.bfloat16 if self.device == "cuda" else torch.float32,
        )
        print("Model loaded successfully!")
        return self.pipeline
    
    def prepare_time_series(self, df, city, road_type):
        mask = (df['city'] == city) & (df['road_type'] == road_type)
        series = df[mask].sort_values('timestamp')['traffic_density'].values
        return torch.tensor(series, dtype=torch.float32)
    
    def predict_future(self, historical_data, prediction_length=12):
        if not _HAS_CHRONOS or self.pipeline is None:
            raise RuntimeError("Chronos model is not loaded.")

        context = torch.tensor(historical_data[-100:], dtype=torch.float32)
        
        forecast = self.pipeline.predict(
            context,
            prediction_length=prediction_length,
        )
        
        predictions = np.median(forecast[0].numpy(), axis=0)
        return predictions
    
    def classify_congestion(self, traffic_density):
        if traffic_density < 30:
            return 'low'
        elif traffic_density < 60:
            return 'medium'
        else:
            return 'high'
    
    def generate_predictions(self, df, cities, road_types, hours_ahead=[1, 3]):
        predictions = []
        
        for city in cities:
            for road_type in road_types:
                try:
                    historical = self.prepare_time_series(df, city, road_type).numpy()
                    
                    if len(historical) < 50:
                        continue
                    
                    max_hours = max(hours_ahead)
                    future_predictions = self.predict_future(historical, prediction_length=max_hours)
                    
                    last_timestamp = df[(df['city'] == city) & (df['road_type'] == road_type)]['timestamp'].max()
                    
                    for i in range(max_hours):
                        pred_time = last_timestamp + timedelta(hours=i+1)
                        pred_density = float(future_predictions[i])
                        
                        predictions.append({
                            'timestamp': pred_time,
                            'city': city,
                            'road_type': road_type,
                            'predicted_traffic_density': pred_density,
                            'congestion_level': self.classify_congestion(pred_density)
                        })
                        
                except Exception as e:
                    print(f"Error predicting for {city} - {road_type}: {e}")
                    continue
        
        return pd.DataFrame(predictions)
    
    def find_peak_windows(self, predictions_df, city, hours=24):
        city_data = predictions_df[predictions_df['city'] == city].copy()
        
        if len(city_data) == 0:
            return []
        
        city_data = city_data.sort_values('timestamp')
        city_data['hour'] = pd.to_datetime(city_data['timestamp']).dt.hour
        
        peak_hours = city_data.nlargest(5, 'predicted_traffic_density')
        
        peaks = []
        for _, row in peak_hours.iterrows():
            peaks.append({
                'time': row['timestamp'].strftime('%H:%M'),
                'hour': int(row['hour']),
                'traffic_density': float(row['predicted_traffic_density']),
                'congestion_level': row['congestion_level'],
                'road_type': row['road_type']
            })
        
        return peaks
    
    def save_model_artifacts(self, scaler_path):
        joblib.dump(self.scaler, scaler_path)
        print(f"Scaler saved to {scaler_path}")

class TrafficPredictionService:
    def __init__(self, features_path, predictions_path=None):
        self.features_path = features_path
        self.predictions_path = predictions_path
        self.forecaster = TrafficForecaster()
        self.df = None
        self.predictions_df = None
        
    def initialize(self):
        print("Initializing Traffic Prediction Service...")
        self.forecaster.load_model()
        self.df = pd.read_csv(self.features_path)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        
        if self.predictions_path and Path(self.predictions_path).exists():
            try:
                self.predictions_df = pd.read_csv(self.predictions_path)
                if len(self.predictions_df) > 0:
                    self.predictions_df['timestamp'] = pd.to_datetime(self.predictions_df['timestamp'])
                    print("Loaded existing predictions")
            except Exception as e:
                print(f"Could not load existing predictions: {e}")
                self.predictions_df = None
        
        return self
    
    def generate_and_save_predictions(self, output_path):
        cities = self.df['city'].unique()[:3]
        road_types = self.df['road_type'].unique()
        
        print(f"Generating predictions for {len(cities)} cities and {len(road_types)} road types...")
        
        self.predictions_df = self.forecaster.generate_predictions(
            self.df, 
            cities=cities, 
            road_types=road_types,
            hours_ahead=[1, 2, 3, 6, 12, 24]
        )
        
        self.predictions_df.to_csv(output_path, index=False)
        print(f"Predictions saved to {output_path}")
        print(f"Generated {len(self.predictions_df)} predictions")
        
        return self.predictions_df
    
    def get_predictions_for_route(self, city, start_time_str, hours_ahead=3):
        if self.predictions_df is None or len(self.predictions_df) == 0:
            return self._generate_fallback_predictions(city, start_time_str, hours_ahead)
        
        try:
            start_time = datetime.strptime(start_time_str, '%H:%M')
            current_date = datetime.now().date()
            start_datetime = datetime.combine(current_date, start_time.time())
            
            city_predictions = self.predictions_df[self.predictions_df['city'] == city].copy()
            
            if len(city_predictions) == 0:
                return self._generate_fallback_predictions(city, start_time_str, hours_ahead)
            
            city_predictions['pred_hour'] = pd.to_datetime(city_predictions['timestamp']).dt.hour
            target_hour = start_datetime.hour
            
            predictions = []
            for i in range(hours_ahead * 4):
                time_offset = timedelta(minutes=i * 15)
                pred_time = start_datetime + time_offset
                hour = pred_time.hour
                
                hour_data = city_predictions[city_predictions['pred_hour'] == hour]
                
                if len(hour_data) > 0:
                    avg_density = hour_data['predicted_traffic_density'].mean()
                    congestion = self.forecaster.classify_congestion(avg_density)
                else:
                    avg_density = 50
                    congestion = 'medium'
                
                predictions.append({
                    'time': pred_time.strftime('%H:%M'),
                    'congestion_index': int(avg_density),
                    'level': congestion
                })
            
            return predictions
            
        except Exception as e:
            print(f"Error getting predictions: {e}")
            return self._generate_fallback_predictions(city, start_time_str, hours_ahead)
    
    def _generate_fallback_predictions(self, city, start_time_str, hours_ahead):
        start_time = datetime.strptime(start_time_str, '%H:%M')
        predictions = []
        
        for i in range(hours_ahead * 4):
            time_offset = timedelta(minutes=i * 15)
            pred_time = start_time + time_offset
            hour = pred_time.hour + pred_time.minute / 60
            
            if 7.5 <= hour <= 9 or 17 <= hour <= 19:
                congestion = np.random.randint(70, 95)
                level = 'high'
            elif 6 <= hour < 7.5 or 9 < hour <= 10 or 16 <= hour < 17:
                congestion = np.random.randint(45, 70)
                level = 'medium'
            else:
                congestion = np.random.randint(20, 45)
                level = 'low'
            
            predictions.append({
                'time': pred_time.strftime('%H:%M'),
                'congestion_index': congestion,
                'level': level
            })
        
        return predictions
    
    def get_peak_windows(self, city):
        if self.predictions_df is None or len(self.predictions_df) == 0:
            return []
        
        return self.forecaster.find_peak_windows(self.predictions_df, city)

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent.parent
    features_path = base_path / "datasets" / "traffic_features.csv"
    predictions_path = base_path / "datasets" / "traffic_predictions.csv"
    
    service = TrafficPredictionService(features_path, predictions_path)
    service.initialize()
    
    print("\nGenerating predictions...")
    predictions_df = service.generate_and_save_predictions(predictions_path)
    
    print("\nSample predictions:")
    print(predictions_df.head(10))
    
    print("\nCongestion level distribution:")
    print(predictions_df['congestion_level'].value_counts())
