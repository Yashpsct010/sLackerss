import os
import sqlite3
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from typing import List, Any
import uuid

USE_DYNAMODB = os.environ.get("USE_DYNAMODB", "false").lower() == "true"
DYNAMODB_REGION = os.environ.get("DYNAMODB_REGION", "us-east-1")
INVENTORY_TABLE = os.environ.get("INVENTORY_TABLE", "Inventory")
SALES_TABLE = os.environ.get("SALES_TABLE", "SalesHistory")

def _get_sqlite_path() -> str:
    # Handle paths robustly depending on where this is called from
    # Usually executed from backend dir, but could be tests. 
    # Use relative path from this file
    return os.path.join(os.path.dirname(__file__), "..", "..", "..", "inventory.sqlite")

def _get_dynamodb_resource():
    return boto3.resource('dynamodb', region_name=DYNAMODB_REGION)

def get_total_skus() -> int:
    if USE_DYNAMODB:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(INVENTORY_TABLE)
        try:
            response = table.scan(ProjectionExpression="sku")
            items = response.get('Items', [])
            skus = {item['sku'] for item in items if 'sku' in item}
            return len(skus)
        except ClientError:
            return 0
    else:
        db_path = _get_sqlite_path()
        if not os.path.exists(db_path):
            return 0
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(DISTINCT sku) FROM inventory")
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0

def get_locations() -> List[str]:
    if USE_DYNAMODB:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(INVENTORY_TABLE)
        try:
            response = table.scan(ProjectionExpression="#loc", ExpressionAttributeNames={"#loc": "location"})
            items = response.get('Items', [])
            locations = {item['location'] for item in items if 'location' in item}
            return list(locations)
        except ClientError:
            return []
    else:
        db_path = _get_sqlite_path()
        if not os.path.exists(db_path):
            return []
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT DISTINCT location FROM inventory")
        rows = c.fetchall()
        conn.close()
        return [row[0] for row in rows]

def get_skus_by_location(location: str) -> List[str]:
    if USE_DYNAMODB:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(INVENTORY_TABLE)
        try:
            response = table.scan(
                FilterExpression="#loc = :loc",
                ExpressionAttributeNames={"#loc": "location"},
                ExpressionAttributeValues={":loc": location},
                ProjectionExpression="sku"
            )
            items = response.get('Items', [])
            return list({item['sku'] for item in items if 'sku' in item})
        except ClientError:
            return []
    else:
        db_path = _get_sqlite_path()
        if not os.path.exists(db_path):
            return []
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT DISTINCT sku FROM inventory WHERE location=?", (location,))
        rows = c.fetchall()
        conn.close()
        return [row[0] for row in rows]

def get_current_inventory(sku: str, location: str) -> int:
    if USE_DYNAMODB:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(INVENTORY_TABLE)
        try:
            # Assuming partition key 'sku', sort key 'location'
            response = table.get_item(Key={'sku': sku, 'location': location})
            item = response.get('Item')
            return int(item.get('current_quantity', 0)) if item else 0
        except ClientError:
            return 0
    else:
        db_path = _get_sqlite_path()
        if not os.path.exists(db_path):
            return 0
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT current_quantity FROM inventory WHERE sku=? AND location=?", (sku, location))
        row = c.fetchone()
        conn.close()
        return row[0] if row else 0

def restock_item_in_db(sku: str, quantity: int) -> bool:
    if USE_DYNAMODB:
        dynamodb = _get_dynamodb_resource()
        table = dynamodb.Table(INVENTORY_TABLE)
        try:
            # Update all locations for this SKU
            response = table.query(KeyConditionExpression=Key('sku').eq(sku))
            for item in response.get('Items', []):
                table.update_item(
                    Key={'sku': sku, 'location': item['location']},
                    UpdateExpression="ADD current_quantity :q",
                    ExpressionAttributeValues={":q": quantity}
                )
            return True
        except ClientError:
            return False
    else:
        db_path = _get_sqlite_path()
        if not os.path.exists(db_path):
            return False
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("UPDATE inventory SET current_quantity = current_quantity + ? WHERE sku = ?", (quantity, sku))
        conn.commit()
        conn.close()
        return True

def ingest_sales_batch_to_db(valid_records: List[Any]) -> None:
    if not valid_records:
        return
        
    if USE_DYNAMODB:
        from decimal import Decimal
        dynamodb = _get_dynamodb_resource()
        sales_table = dynamodb.Table(SALES_TABLE)
        inventory_table = dynamodb.Table(INVENTORY_TABLE)
        
        with sales_table.batch_writer() as batch:
            for record in valid_records:
                promo = 1 if record.promotion_active else 0
                item_date = record.date.strftime("%Y-%m-%d")
                record_id = str(uuid.uuid4())
                
                batch.put_item(Item={
                    'id': record_id,
                    'date': item_date,
                    'sku': record.sku,
                    'location': record.location,
                    'quantity_sold': record.quantity_sold,
                    # DynamoDB requires floats to be Decimal
                    'price': Decimal(str(record.price)), 
                    'revenue': Decimal(str(record.revenue)),
                    'promotion_active': promo
                })
                
                try:
                    inventory_table.update_item(
                        Key={'sku': record.sku, 'location': record.location},
                        UpdateExpression="ADD current_quantity :q",
                        ExpressionAttributeValues={":q": -record.quantity_sold}
                    )
                except ClientError as e:
                    print(f"Error updating DynamoDB inventory for {record.sku}: {e}")
    else:
        db_path = _get_sqlite_path()
        if not os.path.exists(db_path):
            raise Exception("Database not found")
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        for record in valid_records:
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
            c.execute('''
                UPDATE inventory 
                SET current_quantity = current_quantity - ? 
                WHERE sku = ? AND location = ?
            ''', (record.quantity_sold, record.sku, record.location))
        conn.commit()
        conn.close()
