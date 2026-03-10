import pandas as pd
import numpy as np
from pathlib import Path

class TrafficFeatureEngineer:
    def __init__(self, dataset_path):
        self.dataset_path = dataset_path
        self.df = None
        
    def load_data(self):
        self.df = pd.read_csv(self.dataset_path)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df = self.df.sort_values(['city', 'road_type', 'timestamp'])
        return self.df
    
    def create_lag_features(self, n_lags=3):
        lag_cols = []
        for city in self.df['city'].unique():
            for road in self.df['road_type'].unique():
                mask = (self.df['city'] == city) & (self.df['road_type'] == road)
                for i in range(1, n_lags + 1):
                    col_name = f'lag_{i}'
                    if col_name not in lag_cols:
                        lag_cols.append(col_name)
                    self.df.loc[mask, col_name] = self.df.loc[mask, 'traffic_density'].shift(i)
        return self.df
    
    def create_rolling_features(self, windows=[3, 6, 12]):
        for city in self.df['city'].unique():
            for road in self.df['road_type'].unique():
                mask = (self.df['city'] == city) & (self.df['road_type'] == road)
                for window in windows:
                    col_name = f'rolling_mean_{window}'
                    self.df.loc[mask, col_name] = self.df.loc[mask, 'traffic_density'].rolling(window=window, min_periods=1).mean()
                    
                    col_name = f'rolling_std_{window}'
                    self.df.loc[mask, col_name] = self.df.loc[mask, 'traffic_density'].rolling(window=window, min_periods=1).std()
        return self.df
    
    def create_time_features(self):
        self.df['hour'] = self.df['timestamp'].dt.hour
        self.df['day_of_week_num'] = self.df['timestamp'].dt.dayofweek
        self.df['is_weekend'] = (self.df['day_of_week_num'] >= 5).astype(int)
        self.df['is_rush_hour'] = ((self.df['hour'] >= 7) & (self.df['hour'] <= 9) | 
                                    (self.df['hour'] >= 17) & (self.df['hour'] <= 19)).astype(int)
        return self.df
    
    def encode_categorical(self):
        self.df['city_encoded'] = pd.Categorical(self.df['city']).codes
        self.df['road_type_encoded'] = pd.Categorical(self.df['road_type']).codes
        self.df['day_of_week_encoded'] = pd.Categorical(self.df['day_of_week']).codes
        return self.df
    
    def process_all(self):
        print("Loading data...")
        self.load_data()
        
        print("Creating lag features...")
        self.create_lag_features(n_lags=3)
        
        print("Creating rolling features...")
        self.create_rolling_features(windows=[3, 6, 12])
        
        print("Creating time features...")
        self.create_time_features()
        
        print("Encoding categorical variables...")
        self.encode_categorical()
        
        self.df = self.df.dropna()
        
        return self.df
    
    def save_features(self, output_path):
        self.df.to_csv(output_path, index=False)
        print(f"Features saved to {output_path}")
        return output_path

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent.parent
    dataset_path = base_path / "datasets" / "traffic_dataset.csv"
    output_path = base_path / "datasets" / "traffic_features.csv"
    
    engineer = TrafficFeatureEngineer(dataset_path)
    df_features = engineer.process_all()
    engineer.save_features(output_path)
    
    print(f"\nFeature engineering complete!")
    print(f"Original shape: {pd.read_csv(dataset_path).shape}")
    print(f"Features shape: {df_features.shape}")
    print(f"\nFeature columns: {list(df_features.columns)}")
