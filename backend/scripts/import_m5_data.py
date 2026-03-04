import pandas as pd
import sqlite3
import os
from datetime import datetime

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "inventory.sqlite")
SALES_CSV = os.path.join(BASE_DIR, "sales_train_validation.csv")
CALENDAR_CSV = os.path.join(BASE_DIR, "calendar.csv")
PRICES_CSV = os.path.join(BASE_DIR, "sell_prices.csv")

# We will select 3 specific items to act as our ELEC, FASH, and GROC equivalents
# to prevent the local XGBoost from training 30,490 different models, which would take days.
TARGET_ITEMS = [
    "HOBBIES_1_001", # We'll use this as our "ELEC-100" equivalent
    "HOUSEHOLD_1_001", # We'll use this as our "FASH-200" equivalent
    "FOODS_1_001" # We'll use this as our "GROC-300" equivalent
]
TARGET_STORE = "CA_1" # Just looking at one California warehouse

def import_m5_data():
    print(f"[{datetime.utcnow()}] Starting M5 Dataset Ingestion...")
    
    if not all([os.path.exists(SALES_CSV), os.path.exists(CALENDAR_CSV), os.path.exists(PRICES_CSV)]):
        print("ERROR: Kaggle CSV files not found!")
        print(f"Please download the dataset and ensure these 3 files are in {BASE_DIR}:")
        print(" - sales_train_validation.csv")
        print(" - calendar.csv")
        print(" - sell_prices.csv")
        return

    print("Loading datasets (this may take a minute due to file size)...")
    
    # 1. Load Calendar to map 'd_1' to actual real dates
    cal_df = pd.read_csv(CALENDAR_CSV)
    date_mapping = dict(zip(cal_df['d'], cal_df['date']))
    wm_yr_wk_mapping = dict(zip(cal_df['d'], cal_df['wm_yr_wk']))
    
    # 2. Load Sales Data and filter to our 3 items to save RAM
    sales_df = pd.read_csv(SALES_CSV)
    sales_df = sales_df[(sales_df['item_id'].isin(TARGET_ITEMS)) & (sales_df['store_id'] == TARGET_STORE)]
    
    if sales_df.empty:
        print("Error: Could not find target items in sales data.")
        return
        
    # Melt the dataframe from wide (d_1, d_2...) to long format
    print("Reshaping sales data...")
    id_vars = ['id', 'item_id', 'dept_id', 'cat_id', 'store_id', 'state_id']
    melted_df = pd.melt(sales_df, id_vars=id_vars, var_name='d', value_name='quantity_sold')
    
    # Map 'd_xx' to actual dates and accounting weeks
    melted_df['date'] = melted_df['d'].map(date_mapping)
    melted_df['wm_yr_wk'] = melted_df['d'].map(wm_yr_wk_mapping)
    
    # 3. Load Prices to calculate Revenue
    print("Mapping prices and calculating revenue...")
    prices_df = pd.read_csv(PRICES_CSV)
    prices_df = prices_df[(prices_df['item_id'].isin(TARGET_ITEMS)) & (prices_df['store_id'] == TARGET_STORE)]
    
    # Merge on item, store, and the specific Walmart week
    final_df = pd.merge(melted_df, prices_df, on=['store_id', 'item_id', 'wm_yr_wk'], how='left')
    
    # Fill missing prices with previous known price, or a default
    final_df['sell_price'] = final_df['sell_price'].fillna(method='ffill').fillna(9.99)
    final_df['revenue'] = final_df['quantity_sold'] * final_df['sell_price']
    
    # Simplify column names to match our FastAPI Pydantic schema
    final_df = final_df.rename(columns={'item_id': 'sku', 'store_id': 'location', 'sell_price': 'price'})
    final_df['promotion_active'] = 0 # M5 uses SNAP days, but we'll default to 0 for simplicity
    
    # Keep only what we need for the database
    db_df = final_df[['date', 'sku', 'location', 'quantity_sold', 'price', 'revenue', 'promotion_active']]
    
    print(f"Processed {len(db_df)} total historical records. Writing to SQLite...")
    
    # 4. Insert into SQLite
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Clear old mock data
    c.execute("DELETE FROM sales_history")
    
    # Insert new M5 data
    db_df.to_sql('sales_history', conn, if_exists='append', index=False)
    
    # Ensure items exist in the warehouse inventory table
    c.execute("DELETE FROM inventory")
    for item in TARGET_ITEMS:
        c.execute(
            "INSERT INTO inventory (sku, location, current_quantity) VALUES (?, ?, ?)",
            (item, TARGET_STORE, 300) # Give them 300 starting stock
        )
        
    conn.commit()
    conn.close()
    
    print(f"[{datetime.utcnow()}] Successfully imported Kaggle M5 Data into inventory.sqlite!")
    print(f"You can now run 'python scripts/retrain_models.py' to train the XGBoost engine on {TARGET_ITEMS}.")

if __name__ == "__main__":
    import_m5_data()
