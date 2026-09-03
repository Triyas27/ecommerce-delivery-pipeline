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

## Running locally

1. Set up the Python env and install deps: `py -3.12 -m venv .venv && .venv/Scripts/pip install -r requirements.txt`
2. Download the [Olist dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) into `data/raw/` (requires a Kaggle account/API token)
3. Load raw data into DuckDB: `.venv/Scripts/python scripts/load_raw.py`
4. Build the dbt models: `cd dbt && DBT_PROFILES_DIR=$(pwd) ../.venv/Scripts/dbt build`
5. Train the model **inside Docker** (not locally) so MLflow records container-native artifact paths that the API can later resolve:
   ```
   docker compose run --rm -v "$(pwd)/data:/app/data" -v "$(pwd)/ml:/app/ml" api python ml/train.py
   ```
   (Training locally with `python ml/train.py` works fine for experimentation/MLflow UI browsing, but the resulting `mlflow.db` won't be readable from inside the API container - see note below.)
6. Start the API: `docker compose up -d`, then check `http://localhost:8000/docs`
7. Generate a data drift report: `.venv/Scripts/pip install -r requirements-dev.txt` then `.venv/Scripts/python -m ml.monitor` (must run as `-m ml.monitor`, not `python ml/monitor.py` - the latter puts `ml/` itself on `sys.path` instead of the project root, breaking `from ml.train import ...`). Output goes to `reports/data_drift_report.html` (gitignored - regenerate locally, don't commit it, it's ~4.5MB).

### Why training happens inside Docker

MLflow's local file-based artifact store records the *absolute path* of where a model was saved at training time. If you train locally on Windows, that path looks like `C:/Users/.../mlruns/...` - meaningless inside a Linux container, even with `mlruns/` correctly volume-mounted, since the container is looking for the exact recorded path, not "wherever mlruns happens to be mounted." Training inside a container (reusing the `api` image, with `ml/` and `data/` mounted in temporarily) makes the recorded paths container-native (`/app/mlruns/...`), matching what the API service reads at `/app/mlruns` per `docker-compose.yml`. A production setup would instead use a remote artifact store (S3/GCS/MinIO) addressed by URL instead of filesystem path, avoiding this class of problem entirely - out of scope for a local Docker Compose project.
