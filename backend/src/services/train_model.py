import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
from sklearn.metrics import mean_absolute_percentage_error
from datetime import datetime

# Path where we save the trained models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

def create_features(df):
    """
    Create time series features based on time series index.
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    # Time features
    df['dayofweek'] = df['date'].dt.dayofweek
    df['quarter'] = df['date'].dt.quarter
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    df['dayofyear'] = df['date'].dt.dayofyear
    df['dayofmonth'] = df['date'].dt.day
    df['weekofyear'] = df['date'].dt.isocalendar().week
    
    # Lag features
    df['lag_1'] = df['quantity_sold'].shift(1)
    df['lag_7'] = df['quantity_sold'].shift(7)
    df['lag_30'] = df['quantity_sold'].shift(30)
    
    # Rolling features
    df['rolling_mean_7'] = df['quantity_sold'].shift(1).rolling(window=7).mean()
    df['rolling_mean_30'] = df['quantity_sold'].shift(1).rolling(window=30).mean()
    
    # Fill NAs created by shift/rolling
    df = df.fillna(method='bfill')
    
    return df

def train_model():
    print("Loading historical data...")
    data_path = os.path.join(os.path.dirname(__file__), "..", "..", "historical_sales_data.csv")
    df = pd.read_csv(data_path)
    
    print("Data loaded. Training models for SKUs...")
    skus = df['sku'].unique()
    
    for sku in skus:
        sku_df = df[df['sku'] == sku].copy()
        
        # Feature Engineering
        sku_df = create_features(sku_df)
        
        # Define features and target
        FEATURES = ['dayofweek', 'quarter', 'month', 'year', 'dayofyear', 
                    'dayofmonth', 'weekofyear', 'promotion_active', 
                    'lag_1', 'lag_7', 'lag_30', 'rolling_mean_7', 'rolling_mean_30']
        TARGET = 'quantity_sold'
        
        X = sku_df[FEATURES]
        y = sku_df[TARGET]
        
        # Train-Test split (last 90 days for testing)
        split_idx = len(sku_df) - 90
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Initialize and Train XGBoost Regressor
        reg = xgb.XGBRegressor(
            n_estimators=1000,
            learning_rate=0.01,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            objective='reg:squarederror'
        )
        
        reg.fit(
            X_train, y_train,
            eval_set=[(X_train, y_train), (X_test, y_test)],
            verbose=100
        )
        
        # Evaluate
        predictions = reg.predict(X_test)
        mape = mean_absolute_percentage_error(y_test, predictions)
        print(f"[{sku}] Model trained! MAPE on holdout: {mape:.2%}")
        
        # Save model
        model_path = os.path.join(MODEL_DIR, f"xgboost_{sku}.joblib")
        joblib.dump(reg, model_path)
        print(f"[{sku}] Model saved to {model_path}")
        
        # Save last known features for forecasting context
        last_context = sku_df.iloc[-30:][['date', 'quantity_sold', 'promotion_active']].to_dict('records')
        context_path = os.path.join(MODEL_DIR, f"context_{sku}.joblib")
        joblib.dump(last_context, context_path)
        
    print("All models trained and saved successfully.")

if __name__ == "__main__":
    train_model()
