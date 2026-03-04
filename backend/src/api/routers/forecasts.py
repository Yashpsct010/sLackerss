from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from src.models.domain import Forecast, ForecastHorizon
from src.services.forecasting_engine import generate_forecast

router = APIRouter(prefix="/api/v1/forecasts", tags=["Forecasts"])

@router.get("/{sku}", response_model=Forecast)
async def get_forecast(
    sku: str, 
    horizon: ForecastHorizon = Query(default=ForecastHorizon.DAILY),
    location: Optional[str] = None
):
    try:
        forecast = generate_forecast(sku=sku, horizon=horizon, location=location)
        if not forecast:
            raise HTTPException(status_code=404, detail=f"No data available to forecast for SKU: {sku}")
        return forecast
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
