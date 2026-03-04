import pandas as pd
import numpy as np

# Set random seed for reproducibility
np.random.seed(42)

# Date range
dates = pd.date_range(start="2021-01-01", end="2023-12-31", freq="D")

# SKUs
skus = ["ELEC-100", "FASH-200", "GROC-300"]

data = []

for date in dates:
    day_of_week = date.weekday()  # 0=Monday, 6=Sunday
    month = date.month
    year = date.year

    for sku in skus:
        promotion_active = np.random.rand() < 0.15  # 15% chance

        # --- Base Demand Logic ---
        if sku == "ELEC-100":
            base_demand = 40

            # Black Friday spike (late November)
            if month == 11 and 23 <= date.day <= 30:
                base_demand *= 2.2

            # December holiday spike
            if month == 12:
                base_demand *= 1.8

            noise = np.random.normal(0, 6)
            price = 500 + np.random.normal(0, 20)

        elif sku == "FASH-200":
            base_demand = 120

            # Summer seasonality (May–July)
            if month in [5, 6, 7]:
                base_demand *= 1.4

            # Winter dip
            if month in [1, 2]:
                base_demand *= 0.85

            noise = np.random.normal(0, 15)
            price = 80 + np.random.normal(0, 5)

        elif sku == "GROC-300":
            base_demand = 300

            # Weekend boost
            if day_of_week in [5, 6]:  # Saturday, Sunday
                base_demand *= 1.25

            noise = np.random.normal(0, 25)
            price = 10 + np.random.normal(0, 0.5)

        quantity = base_demand + noise

        # Promotion effect (30–50% spike)
        if promotion_active:
            spike_multiplier = np.random.uniform(1.3, 1.5)
            quantity *= spike_multiplier

        quantity_sold = max(0, int(round(quantity)))
        revenue = round(quantity_sold * price, 2)

        data.append([
            date.strftime("%Y-%m-%d"),
            sku,
            "LOC-1",
            quantity_sold,
            round(price, 2),
            revenue,
            promotion_active
        ])

# Create DataFrame
df = pd.DataFrame(data, columns=[
    "date",
    "sku",
    "location",
    "quantity_sold",
    "price",
    "revenue",
    "promotion_active"
])

# Save to CSV
df.to_csv("historical_sales_data.csv", index=False)

print("Dataset generated successfully: historical_sales_data.csv")