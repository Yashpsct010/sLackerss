from typing import List
from src.models.domain import SalesData
import sqlite3
import os

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
            
    # Insert valid records to SQLite and deduct from inventory
    if valid_records:
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "inventory.sqlite")
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            for record in valid_records:
                # 1. Insert into sales_history
                # Assume boolean for promotion_active maps to integer 1/0
                promo = 1 if record.promotion_active else 0
                c.execute('''
                    INSERT INTO sales_history (date, sku, location, quantity_sold, price, revenue, promotion_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record.date.strftime("%Y-%m-%d"),
                    record.sku,
                    record.location,
                    record.quantity_sold,
                    record.price,
                    record.revenue,
                    promo
                ))
                
                # 2. Deduct from current_inventory
                c.execute('''
                    UPDATE inventory 
                    SET current_quantity = current_quantity - ? 
                    WHERE sku = ? AND location = ?
                ''', (record.quantity_sold, record.sku, record.location))
                
            conn.commit()
            conn.close()
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
