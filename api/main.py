from contextlib import asynccontextmanager
from typing import Optional

import mlflow
import mlflow.sklearn
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

MODEL_NAME = "olist_late_delivery_classifier"
CHAMPION_ALIAS = "champion"

model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    model = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}@{CHAMPION_ALIAS}")
    yield


app = FastAPI(title="Olist Late Delivery Predictor", lifespan=lifespan)


class OrderFeatures(BaseModel):
    promised_days: int
    purchase_day_of_week: int
    purchase_month: int
    item_count: int
    distinct_product_count: int
    distinct_seller_count: int
    total_price: float
    total_freight_value: float
    avg_product_weight_g: Optional[float] = None
    max_product_volume_cm3: Optional[float] = None
    payment_count: Optional[float] = None
    total_payment_value: Optional[float] = None
    max_installments: Optional[float] = None
    customer_seller_distance_km: Optional[float] = None
    customer_state: str
    primary_payment_type: Optional[str] = None


class PredictionResponse(BaseModel):
    is_late_probability: float
    is_late_prediction: bool


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict", response_model=PredictionResponse)
def predict(order: OrderFeatures):
    row = pd.DataFrame([order.model_dump()])
    probability = model.predict_proba(row)[0, 1]
    return PredictionResponse(
        is_late_probability=float(probability),
        is_late_prediction=bool(probability >= 0.5),
    )
