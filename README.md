# SENTINEL — Global Disease Surveillance Dashboard

A full-stack application for monitoring global disease activity using data from multiple public health sources. The system aggregates outbreak reports, health indicators, and case statistics and presents them through an interactive dashboard.

## Quick Start

```bash
git clone <repo-url>
cd project
docker compose up --build
```

Services:

| Service      | URL                                                                  |
| ------------ | -------------------------------------------------------------------- |
| Frontend     | [http://localhost:3000](http://localhost:3000)                       |
| Backend API  | [http://localhost:8000](http://localhost:8000)                       |
| Swagger Docs | [http://localhost:8000/docs](http://localhost:8000/docs)             |
| Health Check | [http://localhost:8000/api/health](http://localhost:8000/api/health) |

---

## Architecture

```
Frontend (Next.js)
       |
       | REST API
       v
Backend (FastAPI)
       |
-----------------------------
| PostgreSQL | Redis | Celery |
-----------------------------
```

### Services

| Service   | Purpose                  | Port |
| --------- | ------------------------ | ---- |
| postgres  | database                 | 5432 |
| redis     | cache and message broker | 6379 |
| backend   | FastAPI server           | 8000 |
| frontend  | Next.js dashboard        | 3000 |
| worker    | Celery background tasks  | —    |
| scheduler | periodic ingestion jobs  | —    |

---

## Data Sources

| Source               | Type    | Data                             |
| -------------------- | ------- | -------------------------------- |
| CDC Content Services | API     | public health topics and reports |
| disease.sh           | API     | COVID-19 global statistics       |
| WHO GHO              | API     | health indicators                |
| ProMED               | RSS     | outbreak alerts                  |
| CDC FluView          | RSS     | influenza surveillance           |
| HealthMap            | scraper | outbreak reports                 |

Data ingestion runs hourly through Celery workers.

---

## API Endpoints

| Endpoint                 | Description                  |
| ------------------------ | ---------------------------- |
| `/api/health`            | service health check         |
| `/api/stats`             | global statistics            |
| `/api/search`            | search diseases or outbreaks |
| `/api/diseases`          | tracked diseases             |
| `/api/outbreaks`         | outbreak reports             |
| `/api/countries`         | list of countries            |
| `/api/country/{name}`    | country statistics           |
| `/api/case-stats`        | time-series case data        |
| `/api/predict/{disease}` | trend prediction             |
| `/api/map-data`          | map visualization data       |
| `/api/events`            | surveillance events feed     |

---

## Machine Learning Components

Trend Prediction
LSTM model that forecasts short-term case trends.

Report Classification
Zero-shot classification used to categorize outbreak reports.

Anomaly Detection
Isolation Forest for detecting abnormal spikes in case counts.

Fallback statistical methods are used when models cannot run.

---

## Frontend

Pages include:

* Dashboard with global statistics and map visualization
* Disease explorer with outbreak reports and predictions
* Country statistics and trend charts
* Analytics for anomaly detection and forecasting

Built with Next.js, React, TypeScript, Tailwind, and Chart.js.

---

## Tech Stack

Backend
Python · FastAPI · SQLAlchemy · Celery · Redis · PostgreSQL

Machine Learning
PyTorch · Transformers · scikit-learn · pandas

Frontend
Next.js · React · TypeScript · Tailwind CSS

Infrastructure
Docker · Docker Compose

---

## Development

Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend

```bash
cd frontend
npm install
npm run dev
```

Celery

```bash
celery -A app.worker worker --loglevel=info
celery -A app.worker beat --loglevel=info
```

Run ingestion manually:

```bash
python -c "from app.worker import run_all_ingestion; run_all_ingestion()"
```

---

## License

MIT


