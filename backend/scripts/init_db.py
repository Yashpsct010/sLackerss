import sqlite3
import os
import pandas as pd

def init_db():
    # Database path
    db_path = os.path.join(os.path.dirname(__file__), "..", "inventory.sqlite")
    
    # Connect
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. Create Inventory Table (ERP System Simulation)
    c.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY, 
            location TEXT, 
            current_quantity INTEGER
        )
    ''')
    
    # Clear existing data
    c.execute("DELETE FROM inventory")
    
    # Insert realistic starting inventory
    # ELEC-100: low stock, high demand
    # FASH-200: healthy
    # GROC-300: overstock
    inventory_data = [
        ('ELEC-100', 'LOC-1', 12),
        ('FASH-200', 'LOC-1', 450),
        ('GROC-300', 'LOC-1', 8200)
    ]
    
    c.executemany("INSERT INTO inventory VALUES (?, ?, ?)", inventory_data)
    
    # 2. Create historical sales table and load the generated CSV 
    # to make it completely queryable.
    print("Loading historical sales to SQLite database...")
    csv_path = os.path.join(os.path.dirname(__file__), "..", "historical_sales_data.csv")
    
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df.to_sql('sales_history', conn, if_exists='replace', index=False)
        print("Inserted historical sales records to DB.")
    else:
        print("Warning: historical_sales_data.csv not found.")
        
    conn.commit()
    conn.close()
    
    print(f"Database successfully initialized at: {db_path}")

if __name__ == "__main__":
    # Ensure scripts dir exists
    os.makedirs(os.path.join(os.path.dirname(__file__)), exist_ok=True)
    init_db()
