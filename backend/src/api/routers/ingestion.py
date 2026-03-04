from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from pydantic import BaseModel
import logging

from src.services.data_ingestion import ingest_sales_batch
from src.services.alert_system import trigger_alerts_for_batch

router = APIRouter(prefix="/api/v1", tags=["Data Ingestion"])

class SalesBatchRequest(BaseModel):
    records: List[Dict[str, Any]]

@router.post("/sales-data")
async def receive_sales_data(request: SalesBatchRequest, background_tasks: BackgroundTasks):
    if not request.records:
        raise HTTPException(status_code=400, detail="Empty batch provided")
        
    result = ingest_sales_batch(request.records)
    
    if result["status"] == "failed":
        raise HTTPException(status_code=422, detail=result)
        
    # Queue the Alert System to run asynchronously after the DB is written
    background_tasks.add_task(trigger_alerts_for_batch, request.records)

    return {"message": "Data processed", "result": result}
    
@router.post("/mock-webhook")
async def receive_mock_webhook(payload: dict):
    # This acts as the receiving end of the Alert system for demonstration
    logging.warning(f"🔔 WEBHOOK RECEIVED: {payload.get('message')}")
    return {"status": "ok"}
