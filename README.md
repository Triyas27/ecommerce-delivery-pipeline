# Olist Delivery & Order Analytics Pipeline

End-to-end data/ML pipeline built on the [Olist Brazilian E-Commerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) dataset.

Raw data -> DuckDB -> dbt (staging/marts) -> Dagster orchestration -> model training (scikit-learn + MLflow) -> FastAPI serving -> Docker Compose -> Evidently monitoring.

## Status

Work in progress. See `PROGRESS.md` (coming soon) for current stage.

## Stack

- **Storage:** DuckDB
- **Transform:** dbt
- **Orchestration:** Dagster
- **Model training/tracking:** scikit-learn, MLflow
- **Serving:** FastAPI
- **Containerization:** Docker Compose
- **Monitoring:** Evidently AI
- **CI:** GitHub Actions
