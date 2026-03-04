from datetime import date, datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field

class ForecastHorizon(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

class AlertType(str, Enum):
    STOCKOUT = "STOCKOUT"
    OVERSTOCK = "OVERSTOCK"
    ACCURACY_DEGRADATION = "ACCURACY_DEGRADATION"
    DATA_QUALITY = "DATA_QUALITY"

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

class TimePeriod(str, Enum):
    DAY_1 = "1_DAY"
    DAY_7 = "7_DAY"
    DAY_30 = "30_DAY"
    MONTH_3 = "3_MONTH"

# --- Data Models ---

class SalesData(BaseModel):
    sku: str = Field(..., max_length=100)
    date: date
    location: str = Field(..., max_length=100)
    quantity_sold: int = Field(..., ge=0)
    revenue: float = Field(..., ge=0.0)
    price: float = Field(..., ge=0.0)
    promotion_active: bool = False

class Prediction(BaseModel):
    date: date
    point_forecast: float
    lower_bound: float
    upper_bound: float
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0)

class AccuracyMetrics(BaseModel):
    sku: str
    period: TimePeriod
    mape: float
    rmse: float
    mae: float
    bias: float
    sample_size: int = Field(..., ge=0)

class Forecast(BaseModel):
    sku: str
    location: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    horizon: ForecastHorizon
    predictions: List[Prediction]
    model_used: str
    accuracy_metrics: Optional[AccuracyMetrics] = None

class OrderRecommendation(BaseModel):
    sku: str
    location: str
    recommended_order_quantity: int = Field(..., ge=0)
    order_by_date: date
    current_inventory: int
    reorder_point: int = Field(..., ge=0)
    safety_stock: int = Field(..., ge=0)
    forecasted_demand: float = Field(..., ge=0.0)
    priority_score: float
    estimated_stockout_date: Optional[date] = None
    recommended_actions: List[str] = []

class Alert(BaseModel):
    id: str
    type: AlertType
    sku: str
    location: Optional[str] = None
    priority: Priority
    created_at: datetime = Field(default_factory=datetime.utcnow)
    message: str
    details: Dict[str, Any] = {}
    recommended_actions: List[str] = []
    status: AlertStatus = AlertStatus.ACTIVE

class FeatureSet(BaseModel):
    sku: str
    features: Dict[str, List[float]] = {}
    feature_names: List[str] = []
    target: List[float] = []
    dates: List[date] = []

class SeasonalityProfile(BaseModel):
    sku: str
    has_weekly_seasonality: bool
    has_monthly_seasonality: bool
    has_yearly_seasonality: bool
    seasonal_periods: List[int] = []
    seasonal_strength: float
    trend_strength: float
