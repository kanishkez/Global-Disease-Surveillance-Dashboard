# Global Disease Surveillance Dashboard — SENTINEL

A production-ready full-stack web application for real-time global disease surveillance, built for hackathon-grade rapid deployment.

![Dashboard](https://img.shields.io/badge/status-production--ready-brightgreen) ![Python](https://img.shields.io/badge/python-3.11-blue) ![Next.js](https://img.shields.io/badge/next.js-14-black) ![Docker](https://img.shields.io/badge/docker-compose-2496ED)

---

## 🚀 Quick Start

```bash
# Clone and run
git clone <repo-url>
cd project

# Launch all 6 services
docker compose up --build
```

Once running:
- **Frontend Dashboard**: [http://localhost:3000](http://localhost:3000)
- **Backend API / Swagger**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 📐 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                     │
│         Dashboard · Maps · Charts · Analytics            │
│                  http://localhost:3000                    │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────┐
│                    Backend (FastAPI)                      │
│         /api/search · /api/outbreaks · /api/predict      │
│                  http://localhost:8000                    │
├──────────────┬──────────────┬────────────────────────────┤
│  PostgreSQL  │    Redis     │   Celery Workers           │
│   (Data)     │   (Cache)    │   (Ingestion Pipeline)     │
└──────────────┴──────────────┴────────────────────────────┘
```

### Docker Services (6)

| Service     | Purpose                          | Port  |
|-------------|----------------------------------|-------|
| `postgres`  | Primary database                 | 5432  |
| `redis`     | Cache + Celery broker            | 6379  |
| `backend`   | FastAPI API server               | 8000  |
| `frontend`  | Next.js dashboard                | 3000  |
| `worker`    | Celery task workers              | —     |
| `scheduler` | Celery Beat (hourly jobs)        | —     |

---

## 📡 Data Sources

| Source                | Type       | Frequency | Data                          |
|-----------------------|------------|-----------|-------------------------------|
| CDC Content Services  | REST API   | 1 hour    | Surveillance reports, topics  |
| disease.sh            | REST API   | 1 hour    | COVID-19 global/country stats |
| WHO GHO               | REST API   | 1 hour    | Health indicators, countries  |
| ProMED Mail           | RSS Feed   | 1 hour    | Disease alerts, outbreaks     |
| CDC FluView           | RSS Feed   | 1 hour    | Influenza surveillance        |
| HealthMap             | Scraper    | 1 hour    | Outbreak alerts, disease news |

---

## 🔌 API Endpoints

| Endpoint                      | Description                    |
|-------------------------------|--------------------------------|
| `GET /api/health`             | Health check                   |
| `GET /api/stats`              | Global statistics              |
| `GET /api/search?q=flu`       | Search diseases/outbreaks      |
| `GET /api/diseases`           | List tracked diseases          |
| `GET /api/outbreaks`          | Active outbreak reports        |
| `GET /api/countries`          | Country list                   |
| `GET /api/country/{name}`     | Country detail + stats         |
| `GET /api/case-stats`         | Case statistics time-series    |
| `GET /api/predict/{disease}`  | ML trend predictions           |
| `GET /api/map-data`           | Map visualization data         |
| `GET /api/events`             | Surveillance events feed       |

---

## 🤖 ML Models

### 1. Outbreak Trend Prediction (PyTorch LSTM)
- 2-layer LSTM with dropout
- Predicts 7-day case forecasts with confidence intervals
- Statistical fallback when insufficient data

### 2. Report Classification (BART Zero-Shot)
- Classifies reports: `confirmed_outbreak`, `suspected_outbreak`, `news_mention`
- Rule-based keyword fallback when model unavailable

### 3. Anomaly Detection (Isolation Forest)
- Detects sudden case spikes using sklearn
- Z-score statistical fallback with rolling-window detection

---

## 🖥️ Frontend Pages

| Page        | Features                                    |
|-------------|---------------------------------------------|
| Dashboard   | Global map, stats cards, alert feed, charts |
| Diseases    | Disease search, predictions, outbreak list  |
| Countries   | Country stats, case trends, outbreak data   |
| Analytics   | ML forecasts, anomaly detection, comparison |

---

## 🛠️ Tech Stack

**Backend**: Python 3.11 · FastAPI · SQLAlchemy · Celery · Redis · PostgreSQL
**ML**: PyTorch · Transformers · scikit-learn · pandas · numpy
**Frontend**: Next.js 14 · React 18 · TypeScript · Tailwind CSS · Chart.js · Leaflet · D3
**Infra**: Docker · Docker Compose

---

## 📂 Project Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entrypoint
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # SQLAlchemy engine
│   │   ├── models.py            # ORM models (6 tables)
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── worker.py            # Celery tasks
│   │   ├── api/routes.py        # API endpoints
│   │   ├── ingestion/           # 6 data ingestors
│   │   └── ml/                  # 3 ML models
│   ├── alembic/                 # DB migrations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages
│   │   ├── components/          # React components
│   │   └── lib/api.ts           # API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## 🔧 Development

```bash
# Backend only
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only
cd frontend
npm install
npm run dev

# Run Celery worker
celery -A app.worker worker --loglevel=info

# Run Celery beat (scheduler)
celery -A app.worker beat --loglevel=info

# Trigger initial data ingestion
python -c "from app.worker import run_all_ingestion; run_all_ingestion()"
```

---

## 📄 License

MIT
