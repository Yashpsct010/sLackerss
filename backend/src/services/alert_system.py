import requests
import sqlite3
import os
from datetime import datetime
from src.models.domain import SalesData

# For demonstration, we'll post to a mock endpoint on our own server or a generic webhook catcher
WEBHOOK_URL = os.environ.get("ALERT_WEBHOOK_URL", "http://localhost:8000/api/v1/mock-webhook")

def trigger_alerts_for_batch(raw_records: list):
    """
    Background worker that runs after a sales batch is ingested.
    It checks if the newly deducted inventory triggered a stockout alert.
    """
    valid_skus = set()
    for record in raw_records:
        if 'sku' in record and 'location' in record:
            valid_skus.add((record['sku'], record['location']))
            
    if not valid_skus:
        return
        
    db_path = os.path.join(os.path.dirname(__file__), "..", "..", "inventory.sqlite")
    if not os.path.exists(db_path):
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    for sku, loc in valid_skus:
        c.execute("SELECT current_quantity FROM inventory WHERE sku=? AND location=?", (sku, loc))
        row = c.fetchone()
        if not row: continue
        
        current_qty = row[0]
        
        try:
            # Query our own recommendation endpoint to see if the AI says we need to reorder
            # In production, cache the reorder points to save DB rounds
            res = requests.get(f"http://localhost:8000/api/v1/recommendations/{loc}")
            if res.status_code == 200:
                recs = res.json().get("recommendations", [])
                for rec in recs:
                    if rec["sku"] == sku:
                        if current_qty <= rec["reorder_point"]:
                            # Active Alert Condition Met - Trigger the Webhook
                            payload = {
                                "timestamp": datetime.utcnow().isoformat(),
                                "alert_type": "CRITICAL_STOCKOUT" if current_qty == 0 else "LOW_STOCK",
                                "sku": sku,
                                "location": loc,
                                "current_inventory": current_qty,
                                "reorder_point": rec["reorder_point"],
                                "recommended_action": rec["recommended_actions"][0],
                                "message": f"🚨 Immediate Action Required: {sku} dropped to {current_qty} units (Reorder Point: {rec['reorder_point']})."
                            }
                            try:
                                requests.post(WEBHOOK_URL, json=payload, timeout=2)
                                print(f"[Alert System] Dispatched Webhook for {sku}")
                            except Exception as e:
                                print(f"[Alert System] Webhook failed (expected if mock URL is down): {e}")
        except Exception as e:
            print(f"[Alert System] Error evaluating alert conditions: {e}")

    conn.close()
