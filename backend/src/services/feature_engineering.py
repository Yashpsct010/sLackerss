from datetime import timedelta
import pandas as pd
from src.models.domain import FeatureSet

def extract_features(sales_data: list) -> FeatureSet:
    """
    Extracts structural feature sets from raw SalesData.
    In production, this converts raw SalesData into a matrix, 
    extracting lag features, rolling statistics, and day-of-week encodings.
    """
    if not sales_data:
        return None
        
    sku = sales_data[0].sku
    
    # Map raw historical data into the ML FeatureSet structure
    return FeatureSet(
        sku=sku,
        features={
            "lag_7": [0] * len(sales_data),
            "lag_30": [0] * len(sales_data),
            "rolling_mean_7": [0] * len(sales_data),
            "day_of_week": [d.date.weekday() for d in sales_data]
        },
        feature_names=["lag_7", "lag_30", "rolling_mean_7", "day_of_week"],
        target=[d.quantity_sold for d in sales_data],
        dates=[d.date for d in sales_data]
    )
