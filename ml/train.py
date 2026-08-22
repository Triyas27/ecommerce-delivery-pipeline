import duckdb
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DB_PATH = "data/olist.duckdb"
SPLIT_DATE = "2018-06-01"

NUMERIC_FEATURES = [
    "promised_days",
    "purchase_day_of_week",
    "purchase_month",
    "item_count",
    "distinct_product_count",
    "distinct_seller_count",
    "total_price",
    "total_freight_value",
    "avg_product_weight_g",
    "max_product_volume_cm3",
    "payment_count",
    "total_payment_value",
    "max_installments",
    "customer_seller_distance_km",
]
CATEGORICAL_FEATURES = ["customer_state", "primary_payment_type"]
TARGET = "is_late"


def load_data() -> pd.DataFrame:
    con = duckdb.connect(DB_PATH)
    df = con.execute("SELECT * FROM fct_orders").fetchdf()
    con.close()
    return df


def time_split(df: pd.DataFrame):
    train = df[df["purchased_at"] < SPLIT_DATE]
    test = df[df["purchased_at"] >= SPLIT_DATE]
    return train, test


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
    ])
    categorical_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
    ])


def evaluate(y_true, y_pred, y_proba) -> dict:
    return {
        "precision": precision_score(y_true, y_pred),
        "recall": recall_score(y_true, y_pred),
        "f1": f1_score(y_true, y_pred),
        "roc_auc": roc_auc_score(y_true, y_proba),
    }


def main():
    mlflow.set_experiment("olist-late-delivery")

    df = load_data()
    train, test = time_split(df)
    print(f"train: {len(train)} rows, test: {len(test)} rows")

    X_train = train[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_train = train[TARGET]
    X_test = test[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y_test = test[TARGET]

    # baseline: always predict the majority class, as a floor to beat
    with mlflow.start_run(run_name="baseline_majority_class"):
        baseline = DummyClassifier(strategy="most_frequent")
        baseline.fit(X_train, y_train)
        y_pred = baseline.predict(X_test)
        y_proba = baseline.predict_proba(X_test)[:, 1]

        metrics = evaluate(y_test, y_pred, y_proba)
        mlflow.log_params({"model": "DummyClassifier", "strategy": "most_frequent"})
        mlflow.log_metrics(metrics)
        print("baseline:", metrics)

    # real model: random forest with class weighting for the imbalance
    with mlflow.start_run(run_name="random_forest_balanced"):
        params = {
            "n_estimators": 300,
            "max_depth": 8,
            "min_samples_leaf": 20,
            "class_weight": "balanced",
            "random_state": 42,
        }
        model = Pipeline([
            ("preprocess", build_preprocessor()),
            ("classify", RandomForestClassifier(**params)),
        ])
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        metrics = evaluate(y_test, y_pred, y_proba)
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(model, "model")
        print("random_forest_balanced:", metrics)


if __name__ == "__main__":
    main()
