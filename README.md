<div align="center">

# MLNet

**Train, compare, and deploy machine learning models without writing a single line of code.**

[![Build](https://img.shields.io/github/actions/workflow/status/wld06/MLNet/ci.yml?branch=main)](https://github.com/wld06/MLNet/actions)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Stars](https://img.shields.io/github/stars/wld06/MLNet?style=social)](https://github.com/wld06/MLNet/stargazers)

</div>

---

MLNest is an open source, self-hostable web platform for the full machine learning lifecycle: upload a CSV, clean and prepare your data visually, launch experiments across multiple algorithms and hyperparameters, and get a production-ready REST endpoint.

Inspired by Azure ML Studio, but free, self-hosted, and focused on explainability and code export.

> **Current status:** backend only. The frontend is in the design phase.

---

## Features

- 📊 **Visual data cleaning** — nulls, duplicates, types, normalization, encoding, outliers, formulas, and string ops, all versioned and immutable from v0.
- 🧪 **Multi-algorithm experiments** — launch algorithm × hyperparameter combinations in parallel with 5-fold cross-validation.
- 🔍 **Built-in explainability** — SHAP, feature importance, confusion matrix, and learning curves per run.
- 🚀 **One-click deploy** — serialize the full pipeline and generate a FastAPI microservice with `POST /predict` and an API key.
- 📦 **Export** — download a deployment as `docker-compose` or a reproducible notebook.
- ⚡ **Real time** — training and cleaning logs over WebSocket.
- 🗂️ **Full tracking** — experiments, metrics, and artifacts in MLflow; datasets and models in S3-compatible storage.

---

## Tech stack

![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![MLflow](https://img.shields.io/badge/MLflow-0194E2?logo=mlflow&logoColor=white)
![MinIO](https://img.shields.io/badge/MinIO-C72E49?logo=minio&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)

- **API:** FastAPI + WebSocket
- **Task queue:** Celery + Redis
- **Data:** PostgreSQL · SQLAlchemy · Alembic
- **ML:** scikit-learn, XGBoost, LightGBM, SHAP, pandas, numpy
- **Tracking & storage:** MLflow · MinIO (S3-compatible)
- **Validation:** Pydantic v2 · great-expectations

---

## Architecture

```
            ┌──────────┐   WS logs    ┌──────────────┐
   Client ──┤ FastAPI  ├──────────────┤  PostgreSQL  │
            └────┬─────┘              └──────────────┘
                 │ enqueue
            ┌────▼──────┐   broker    ┌──────────────┐
            │  Celery   ├─────────────┤    Redis     │
            │  workers  │             └──────────────┘
            └────┬──────┘
       ┌─────────┼──────────┐
  ┌────▼───┐ ┌───▼────┐ ┌───▼────┐
  │ MinIO  │ │ MLflow │ │  ML    │
  │datasets│ │tracking│ │ algos  │
  └────────┘ └────────┘ └────────┘
```

Workers are stateless: all state lives in PostgreSQL or MLflow. Datasets (up to 500 MB) are processed via streaming, never loaded fully into memory.

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- Or, for local development: Python 3.11+, PostgreSQL, Redis, MinIO, and an MLflow server

---

## Installation

### With Docker (recommended)

```bash
git clone https://github.com/wld06/MLNet.git
cd MLNet
docker compose up --build
```

The API is available at `http://localhost:8000` and interactive docs at `http://localhost:8000/docs`.

### Local development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Celery workers, in a separate terminal:

```bash
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
```

Migrations:

```bash
alembic upgrade head
```

---

## Configuration

Environment variables (see `.env.example`):

| Variable                      | Default                                            | Description              |
| ----------------------------- | -------------------------------------------------- | ------------------------ |
| `DATABASE_URL`                | `postgresql://user:password@localhost:5432/mlnest` | PostgreSQL connection    |
| `REDIS_URL`                   | `redis://localhost:6379/0`                         | Celery broker and cache  |
| `MINIO_ENDPOINT`              | `localhost:9000`                                   | Object storage           |
| `MINIO_ACCESS_KEY`            | `minioadmin`                                       | MinIO access key         |
| `MINIO_SECRET_KEY`            | `minioadmin`                                       | MinIO secret key         |
| `MINIO_BUCKET`                | `mlnest-datasets`                                  | Datasets bucket          |
| `MLFLOW_TRACKING_URI`         | `http://localhost:5000`                            | Tracking server          |
| `SECRET_KEY`                  | —                                                  | **Change in production** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60`                                               | Token expiry             |
| `MAX_DATASET_SIZE_MB`         | `500`                                              | Max dataset size         |
| `CLEANING_PREVIEW_ROWS`       | `1000`                                             | Sample rows for previews |
| `CLEANING_CACHE_TTL`          | `3600`                                             | Preview cache TTL (s)    |

---

## API

Full interactive docs at `/docs` (Swagger) and `/redoc`.

<details>
<summary><b>Datasets & versioning</b></summary>

```
POST   /api/datasets/upload
GET    /api/datasets
GET    /api/datasets/{id}
GET    /api/datasets/{id}/preview?rows=50
GET    /api/datasets/{id}/profile
DELETE /api/datasets/{id}
GET    /api/datasets/{id}/versions
GET    /api/datasets/{id}/versions/{v}
POST   /api/datasets/{id}/versions/{v}/export
```

</details>

<details>
<summary><b>Cleaning & preparation</b></summary>

```
# Inspection
GET    /api/datasets/{id}/quality
GET    /api/datasets/{id}/columns/{col}/distribution
GET    /api/datasets/{id}/columns/{col}/outliers
GET    /api/datasets/{id}/correlations

# Nulls / duplicates / types
POST   /api/datasets/{id}/clean/drop-nulls
POST   /api/datasets/{id}/clean/fill-nulls
POST   /api/datasets/{id}/clean/drop-duplicates
POST   /api/datasets/{id}/clean/cast-column
POST   /api/datasets/{id}/clean/parse-dates

# Transformations
POST   /api/datasets/{id}/clean/normalize
POST   /api/datasets/{id}/clean/encode
POST   /api/datasets/{id}/clean/bin-column
POST   /api/datasets/{id}/clean/clip-outliers
POST   /api/datasets/{id}/clean/apply-formula

# Pipeline & versioning
POST   /api/datasets/{id}/clean/preview
POST   /api/datasets/{id}/clean/apply
POST   /api/datasets/{id}/clean/apply-pipeline
GET    /api/datasets/{id}/clean/history
POST   /api/datasets/{id}/clean/rollback/{v}
```

</details>

<details>
<summary><b>Experiments & runs</b></summary>

```
POST   /api/experiments
GET    /api/experiments
GET    /api/experiments/{id}
PUT    /api/experiments/{id}
DELETE /api/experiments/{id}
POST   /api/experiments/{id}/launch
POST   /api/experiments/{id}/stop
GET    /api/experiments/{id}/runs

GET    /api/runs/{id}/metrics
GET    /api/runs/{id}/shap
GET    /api/runs/{id}/feature-importance
GET    /api/runs/{id}/confusion-matrix
POST   /api/runs/{id}/deploy
```

</details>

<details>
<summary><b>Deploy</b></summary>

```
GET    /api/deployments
GET    /api/deployments/{id}
DELETE /api/deployments/{id}
POST   /api/deployments/{id}/predict
GET    /api/deployments/{id}/logs
POST   /api/deployments/{id}/rotate-key
GET    /api/deployments/{id}/export/docker
GET    /api/deployments/{id}/export/notebook
```

</details>

<details>
<summary><b>WebSocket</b></summary>

```
WS     /ws/experiments/{id}
WS     /ws/datasets/{id}/clean
```

</details>

---

## Available algorithms

**Classification:** `logistic_regression`, `random_forest_classifier`, `gradient_boosting_classifier`, `xgboost_classifier`, `lightgbm_classifier`, `svm_classifier`, `knn_classifier`

**Regression:** `linear_regression`, `ridge`, `lasso`, `random_forest_regressor`, `xgboost_regressor`, `lightgbm_regressor`

---

## Project structure

```
backend/
├── app/
│   ├── api/          # Endpoints: datasets, cleaning, experiments, runs, models, deploy
│   ├── core/         # Config, security, dependencies
│   ├── db/           # SQLAlchemy models, session, Alembic migrations
│   ├── schemas/      # Pydantic schemas
│   ├── services/     # Business logic
│   ├── workers/      # Celery tasks (cleaning, training)
│   ├── ml/           # Algorithms, pipelines, metrics, explainability
│   └── main.py
├── tests/
├── Dockerfile
└── requirements.txt
```

---

## Tests

```bash
cd backend && pytest -v
```

Linting and type checking:

```bash
ruff check . && ruff format .
mypy app/
```

---

## Contributing

1. Fork the repository
2. Create a branch: `git checkout -b feat/my-feature`
3. Make sure `ruff`, `mypy`, and `pytest` all pass
4. Open a Pull Request

Code is formatted with **ruff** and type-checked with **mypy strict** on new modules.

---

## License

Distributed under the **MIT** License. See [`LICENSE`](LICENSE) for details.

---

<div align="center">

Made by [@wld06](https://github.com/wld06)

</div>
