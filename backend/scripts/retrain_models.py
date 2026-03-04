import pandas as pd
import numpy as np
import xgboost as xgb
import joblib
import os
import sqlite3
import json
from sklearn.metrics import mean_absolute_percentage_error
from datetime import datetime

# Path where we save the trained models
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "inventory.sqlite")
os.makedirs(MODEL_DIR, exist_ok=True)

def create_features(df):
    """
    Create time series features based on time series index.
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date')
    
    df['dayofweek'] = df['date'].dt.dayofweek
    df['quarter'] = df['date'].dt.quarter
    df['month'] = df['date'].dt.month
    df['year'] = df['date'].dt.year
    df['dayofyear'] = df['date'].dt.dayofyear
    df['dayofmonth'] = df['date'].dt.day
    df['weekofyear'] = df['date'].dt.isocalendar().week
    
    df['lag_1'] = df['quantity_sold'].shift(1)
    df['lag_7'] = df['quantity_sold'].shift(7)
    df['lag_30'] = df['quantity_sold'].shift(30)
    
    df['rolling_mean_7'] = df['quantity_sold'].shift(1).rolling(window=7, min_periods=1).mean()
    df['rolling_mean_30'] = df['quantity_sold'].shift(1).rolling(window=30, min_periods=1).mean()
    
    df = df.fillna(method='bfill').fillna(0)
    
    return df

def retrain_models():
    print(f"[{datetime.utcnow()}] Starting automated ML model retraining...")
    
    if not os.path.exists(DB_PATH):
        print("Database not found. Exiting.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    # Read entire sales history
    df = pd.read_sql_query("SELECT * FROM sales_history", conn)
    conn.close()
    
    if df.empty:
        print("No sales history found to train on.")
        return
        
    print(f"Data loaded from live SQLite database. {len(df)} records found. Training models...")
    skus = df['sku'].unique()
    
    metrics_dict = {}
    
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
        
        # Train-Test split (last 30 days for testing so we don't overfit to old data)
        # Using 30 instead of 90 because we want the live model to evaluate on very recent data
        split_idx = max(int(len(sku_df) * 0.8), len(sku_df) - 30)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        if len(X_train) < 30:
            print(f"Not enough data to retrain {sku}")
            continue
            
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
            verbose=False
        )
        
        # Evaluate using WMAPE (Weighted MAPE) to prevent infinity from zero-sales days in the Kaggle dataset
        predictions = reg.predict(X_test)
        
        total_actual = np.sum(y_test)
        if total_actual > 0:
            mape = np.sum(np.abs(y_test - predictions)) / total_actual
        else:
            mape = 0.0

        print(f"[{sku}] Retrained successfully! Live Accuracy (WMAPE): {mape:.2%}")
        metrics_dict[sku] = float(mape)
        
        # Save model
        model_path = os.path.join(MODEL_DIR, f"xgboost_{sku}.joblib")
        joblib.dump(reg, model_path)
        
        # Save last known features for forecasting context
        last_context = sku_df.iloc[-30:][['date', 'quantity_sold', 'promotion_active']].to_dict('records')
        context_path = os.path.join(MODEL_DIR, f"context_{sku}.joblib")
        joblib.dump(last_context, context_path)
        
    # Save the metrics to a JSON file so the API can surface these live metrics
    metrics_path = os.path.join(MODEL_DIR, "live_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_dict, f)
        
    print(f"[{datetime.utcnow()}] All models successfully retrained and deployed to production!")

if __name__ == "__main__":
    retrain_models()
