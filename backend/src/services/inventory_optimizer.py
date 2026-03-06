import math
from datetime import datetime, timedelta
from src.models.domain import Forecast, OrderRecommendation

def calculate_optimal_order(
    sku: str, 
    forecast: Forecast, 
    current_inventory: int, 
    lead_time_days: int = 5,
    service_level_z_score: float = 1.65 # 95% service level
) -> OrderRecommendation:
    """
    Calculates inventory optimization metrics: Reorder point, safety stock, and EOQ.
    """
    
    # Calculate average daily demand and standard deviation from forecast
    if not forecast.predictions:
        return None
        
    import statistics
    
    daily_demands = [p.point_forecast for p in forecast.predictions]
    avg_daily_demand = sum(daily_demands) / len(daily_demands)
    
    # Calculate actual standard deviation of the forecasted demand
    if len(daily_demands) > 1:
        std_dev_demand = statistics.stdev(daily_demands)
    else:
        std_dev_demand = 0.0
    
    # Safety Stock formula: Z * StdDev * sqrt(Lead Time)
    safety_stock = math.ceil(service_level_z_score * std_dev_demand * math.sqrt(lead_time_days))
    
    # Reorder Point formula: (Avg Daily Demand * Lead Time) + Safety Stock
    reorder_point = math.ceil((avg_daily_demand * lead_time_days) + safety_stock)
    
    # Recommended order size using 30-day supply heuristic 
    # (Replaces EOQ when exact holding/ordering costs are unavailable)
    recommended_order_quantity = math.ceil(avg_daily_demand * 30)
    
    # Estimate stockout
    days_until_stockout = current_inventory / avg_daily_demand if avg_daily_demand > 0 else 999
    stockout_date = None
    if days_until_stockout < 365:
       stockout_date = datetime.utcnow().date() + timedelta(days=int(days_until_stockout))
       
    # Priority based on stockout risk
    priority_score = 100.0 - days_until_stockout
    priority_score = max(0, min(100, priority_score))
    
    actions = []
    if current_inventory <= reorder_point:
        actions.append(f"Place order for {recommended_order_quantity} units immediately.")
    else:
        actions.append("Inventory levels are currently healthy.")

    return OrderRecommendation(
        sku=sku,
        location=forecast.location or "WH-1",
        recommended_order_quantity=recommended_order_quantity,
        order_by_date=datetime.utcnow().date() if current_inventory <= reorder_point else datetime.utcnow().date() + timedelta(days=7),
        current_inventory=current_inventory,
        reorder_point=reorder_point,
        safety_stock=safety_stock,
        forecasted_demand=avg_daily_demand * 30, # Monthly
        priority_score=round(priority_score, 2),
        estimated_stockout_date=stockout_date,
        recommended_actions=actions
    )
