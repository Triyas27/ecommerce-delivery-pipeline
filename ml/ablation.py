import duckdb
import mlflow
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DB_PATH = "data/olist.duckdb"
SPLIT_DATE = "2018-06-01"

BASE_NUMERIC = [
    "promised_days",
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
]
BASE_CATEGORICAL = ["customer_state", "primary_payment_type"]


def run_config(name: str, numeric_features: list, categorical_features: list, train, test):
    X_train = train[numeric_features + categorical_features]
    y_train = train["is_late"]
    X_test = test[numeric_features + categorical_features]
    y_test = test["is_late"]

    numeric_pipeline = Pipeline([("impute", SimpleImputer(strategy="median"))])
    categorical_pipeline = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_features),
        ("categorical", categorical_pipeline, categorical_features),
    ])

    params = {
        "n_estimators": 300,
        "max_depth": 8,
        "min_samples_leaf": 20,
        "class_weight": "balanced",
        "random_state": 42,
    }
    model = Pipeline([
        ("preprocess", preprocessor),
        ("classify", RandomForestClassifier(**params)),
    ])

    with mlflow.start_run(run_name=name):
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]
        metrics = {
            "precision": precision_score(y_test, y_pred),
            "recall": recall_score(y_test, y_pred),
            "f1": f1_score(y_test, y_pred),
            "roc_auc": roc_auc_score(y_test, y_proba),
        }
        mlflow.log_params({**params, "numeric_features": numeric_features, "categorical_features": categorical_features})
        mlflow.log_metrics(metrics)
        print(f"{name}: {metrics}")


def main():
    mlflow.set_experiment("olist-late-delivery")
    con = duckdb.connect(DB_PATH)
    df = con.execute("SELECT * FROM fct_orders").fetchdf()
    con.close()

    train = df[df["purchased_at"] < SPLIT_DATE]
    test = df[df["purchased_at"] >= SPLIT_DATE]

    # isolate: keep month/day numeric (like the original run), only add distance
    run_config(
        "distance_only",
        numeric_features=BASE_NUMERIC + ["customer_seller_distance_km", "purchase_day_of_week", "purchase_month"],
        categorical_features=BASE_CATEGORICAL,
        train=train,
        test=test,
    )

    # isolate: keep the original numeric feature set, only change month/day to categorical
    run_config(
        "month_onehot_only",
        numeric_features=BASE_NUMERIC,
        categorical_features=BASE_CATEGORICAL + ["purchase_day_of_week", "purchase_month"],
        train=train,
        test=test,
    )


if __name__ == "__main__":
    main()
