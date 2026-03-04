from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from src.models.domain import OrderRecommendation, ForecastHorizon
from src.services.forecasting_engine import generate_forecast
from src.services.inventory_optimizer import calculate_optimal_order
from pydantic import BaseModel
import sqlite3
import os

router = APIRouter(prefix="/api/v1/recommendations", tags=["Inventory Optimization"])

class RecommendationResponse(BaseModel):
    recommendations: List[OrderRecommendation]

def get_current_inventory(sku: str, location: str) -> int:
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "inventory.sqlite")
    if not os.path.exists(db_path):
        return 0 # Fallback
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT current_quantity FROM inventory WHERE sku=? AND location=?", (sku, location))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

class RestockRequest(BaseModel):
    quantity: int

@router.post("/{sku}/restock")
async def restock_item(sku: str, request: RestockRequest):
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "inventory.sqlite")
    if not os.path.exists(db_path):
        raise HTTPException(status_code=500, detail="Database not found")
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Simulating a PO receipt by directly updating current_quantity
    c.execute("UPDATE inventory SET current_quantity = current_quantity + ? WHERE sku = ?", (request.quantity, sku))
    conn.commit()
    conn.close()
    
    return {"status": "success", "message": f"Restocked {request.quantity} units of {sku}"}

@router.get("/{location}", response_model=RecommendationResponse)
async def get_recommendations(
    location: str,
    priority: Optional[str] = Query(None, description="Filter by priority, e.g., CRITICAL, HIGH")
):
    mock_skus = ["ELEC-100", "FASH-200", "GROC-300"]
    recommendations = []
    
    for sku in mock_skus:
        forecast = generate_forecast(sku=sku, horizon=ForecastHorizon.DAILY, location=location)
        current_inv = get_current_inventory(sku, location)
        
        rec = calculate_optimal_order(sku=sku, forecast=forecast, current_inventory=current_inv)
        if rec:
            recommendations.append(rec)
            
    # Sort by priority score descending
    recommendations.sort(key=lambda x: x.priority_score, reverse=True)
    
    return {"recommendations": recommendations}
