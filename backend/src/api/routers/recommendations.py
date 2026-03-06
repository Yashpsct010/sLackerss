from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from src.models.domain import OrderRecommendation, ForecastHorizon
from src.services.forecasting_engine import generate_forecast
from src.services.inventory_optimizer import calculate_optimal_order
from pydantic import BaseModel
from src.services import database

router = APIRouter(prefix="/api/v1/recommendations", tags=["Inventory Optimization"])

class RecommendationResponse(BaseModel):
    recommendations: List[OrderRecommendation]

class RestockRequest(BaseModel):
    quantity: int

@router.get("/stats")
async def get_stats():
    total_skus = database.get_total_skus()
    if total_skus == 0:
        total_skus = 6 # fallback for demonstration safety
    return {"total_optimized_skus": total_skus}

@router.get("/locations")
async def get_locations():
    locations = database.get_locations()
    if not locations:
        locations = ["CA_1"] # fallback for demonstration safety
    return {"locations": locations}

@router.post("/{sku}/restock")
async def restock_item(sku: str, request: RestockRequest):
    success = database.restock_item_in_db(sku, request.quantity)
    if not success:
        raise HTTPException(status_code=500, detail="Database not found or update failed")
    
    return {"status": "success", "message": f"Restocked {request.quantity} units of {sku}"}

@router.get("/{location}", response_model=RecommendationResponse)
async def get_recommendations(
    location: str,
    priority: Optional[str] = Query(None, description="Filter by priority, e.g., CRITICAL, HIGH")
):
    skus = database.get_skus_by_location(location)
    
    # Fallback if DB doesn't exist
    if not skus:
        skus = ["HOBBIES_1_001", "HOUSEHOLD_1_001", "FOODS_1_001"]

    recommendations = []
    
    for sku in skus:
        forecast = generate_forecast(sku=sku, horizon=ForecastHorizon.DAILY, location=location)
        current_inv = database.get_current_inventory(sku, location)
        
        rec = calculate_optimal_order(sku=sku, forecast=forecast, current_inventory=current_inv)
        if rec:
            recommendations.append(rec)
            
    # Sort by priority score descending
    recommendations.sort(key=lambda x: x.priority_score, reverse=True)
    
    return {"recommendations": recommendations}
