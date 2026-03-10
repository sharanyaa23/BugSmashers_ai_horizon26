import sys
from pathlib import Path

base_path = Path(__file__).parent.parent.parent
sys.path.append(str(base_path / "server"))

from models.feature_engineering import TrafficFeatureEngineer
from models.traffic_forecaster import TrafficPredictionService

def main():
    print("=" * 60)
    print("TRAFFIC FORECASTING MODEL TRAINING PIPELINE")
    print("=" * 60)
    
    dataset_path = base_path / "datasets" / "traffic_dataset.csv"
    features_path = base_path / "datasets" / "traffic_features.csv"
    predictions_path = base_path / "datasets" / "traffic_predictions.csv"
    
    print("\n[STEP 1/3] Feature Engineering")
    print("-" * 60)
    engineer = TrafficFeatureEngineer(dataset_path)
    df_features = engineer.process_all()
    engineer.save_features(features_path)
    
    print(f"\n✓ Features created: {df_features.shape[0]} rows, {df_features.shape[1]} columns")
    
    print("\n[STEP 2/3] Loading Hugging Face Time-Series Model")
    print("-" * 60)
    service = TrafficPredictionService(features_path, predictions_path)
    service.initialize()
    
    print("\n✓ Chronos model loaded successfully")
    
    print("\n[STEP 3/3] Generating Traffic Predictions")
    print("-" * 60)
    predictions_df = service.generate_and_save_predictions(predictions_path)
    
    print(f"\n✓ Predictions generated: {len(predictions_df)} forecasts")
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE!")
    print("=" * 60)
    
    print("\nOutput Files:")
    print(f"  1. Features: {features_path}")
    print(f"  2. Predictions: {predictions_path}")
    
    if len(predictions_df) > 0:
        print("\nPrediction Summary:")
        print(predictions_df.groupby('congestion_level').size())
        
        print("\nSample Predictions:")
        print(predictions_df.head(10)[['timestamp', 'city', 'predicted_traffic_density', 'congestion_level']])
    else:
        print("\nWarning: No predictions were generated. Check error messages above.")
    
    print("\n✓ Ready for API integration!")

if __name__ == "__main__":
    main()
