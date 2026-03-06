from typing import List
from src.models.domain import SalesData
from src.services.database import ingest_sales_batch_to_db

def ingest_sales_batch(batch: List[dict]) -> dict:
    valid_records = []
    errors = []
    
    for i, record in enumerate(batch):
        try:
            parsed = SalesData(**record)
            if parsed.revenue < 0 or parsed.price <= 0:
                raise ValueError("Revenue and price must be positive numbers")
            valid_records.append(parsed)
        except Exception as e:
            errors.append({"index": i, "error": str(e), "data": record})
            
    # Insert valid records to storage and deduct from inventory
    if valid_records:
        try:
            ingest_sales_batch_to_db(valid_records)
        except Exception as e:
            return {
                "status": "failed",
                "processed": len(valid_records) + len(errors),
                "valid_count": 0,
                "error_count": len(valid_records) + len(errors),
                "errors": [{"error": f"Database error: {str(e)}"}]
            }
            
    return {
        "status": "success" if not errors else "partial_success" if valid_records else "failed",
        "processed": len(valid_records) + len(errors),
        "valid_count": len(valid_records),
        "error_count": len(errors),
        "errors": errors
    }
