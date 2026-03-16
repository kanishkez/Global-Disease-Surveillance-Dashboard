# Test backend models with `curl`

This project exposes **FastAPI** read endpoints under `/api` (backed by SQLAlchemy models like `Disease`, `Country`, `OutbreakReport`, `CaseStatistic`, `SurveillanceEvent`, `TrendPrediction`).

## Start the backend (Docker Compose)

From the repo root:

```bash
docker compose up --build
```

Defaults:
- **Backend**: `http://localhost:8000`
- **Swagger**: `http://localhost:8000/docs`

If you’re calling the API from a different device, replace `localhost` in the commands below with the machine’s IP/hostname (example: `http://192.168.1.50:8000`).

If you have `jq` installed, you can pretty-print JSON:

```bash
curl -s "http://localhost:8000/api/health" | jq
```

## Quick sanity checks

### Root

```bash
curl -s "http://localhost:8000/"
```

### Health

```bash
curl -s "http://localhost:8000/api/health"
```

### Global stats

```bash
curl -s "http://localhost:8000/api/stats"
```

## Search (multi-model)

Search across diseases/outbreaks/countries/events:

```bash
curl -sG "http://localhost:8000/api/search" --data-urlencode "q=flu"
```

Filter outbreaks by region/country (query params are optional):

```bash
curl -sG "http://localhost:8000/api/search" \
  --data-urlencode "q=" \
  --data-urlencode "disease=cholera" \
  --data-urlencode "region=Africa" \
  --data-urlencode "country=Kenya"
```

## Diseases (`Disease`)

List diseases (supports pagination via `skip` and `limit`):

```bash
curl -sG "http://localhost:8000/api/diseases" --data-urlencode "skip=0" --data-urlencode "limit=50"
```

## Outbreaks (`OutbreakReport`)

List outbreaks with optional filters:

```bash
curl -s "http://localhost:8000/api/outbreaks"
```

Filter by disease:

```bash
curl -sG "http://localhost:8000/api/outbreaks" --data-urlencode "disease=cholera"
```

Filter by country:

```bash
curl -sG "http://localhost:8000/api/outbreaks" --data-urlencode "country=India"
```

Filter by severity (expected: `low|medium|high|critical`):

```bash
curl -sG "http://localhost:8000/api/outbreaks" --data-urlencode "severity=high"
```

Include inactive outbreaks too:

```bash
curl -sG "http://localhost:8000/api/outbreaks" --data-urlencode "active_only=false"
```

Paginate:

```bash
curl -sG "http://localhost:8000/api/outbreaks" --data-urlencode "skip=0" --data-urlencode "limit=20"
```

## Countries (`Country`)

List countries:

```bash
curl -s "http://localhost:8000/api/countries"
```

Filter by continent:

```bash
curl -sG "http://localhost:8000/api/countries" --data-urlencode "continent=Europe"
```

Paginate:

```bash
curl -sG "http://localhost:8000/api/countries" --data-urlencode "skip=0" --data-urlencode "limit=100"
```

### Country details (outbreaks + case stats)

This aggregates **country info**, recent **outbreaks**, and up to ~365 days of **case statistics**.

```bash
curl -s "http://localhost:8000/api/country/United%20States"
```

If you’re not sure what country names exist yet, list a few first:

```bash
curl -sG "http://localhost:8000/api/countries" --data-urlencode "limit=10"
```

## Case statistics (`CaseStatistic`)

Get time-series case stats (default `days=30`):

```bash
curl -s "http://localhost:8000/api/case-stats"
```

Filter by disease + country:

```bash
curl -sG "http://localhost:8000/api/case-stats" \
  --data-urlencode "disease=covid" \
  --data-urlencode "country=India" \
  --data-urlencode "days=90"
```

## Predictions (`TrendPrediction`)

Predictions endpoint returns stored predictions if present; otherwise it returns **mock predictions**.

```bash
curl -s "http://localhost:8000/api/predict/covid-19"
```

With country filter:

```bash
curl -sG "http://localhost:8000/api/predict/covid-19" --data-urlencode "country=India"
```

## Map data (computed from multiple models)

Returns per-country points with latest case stats + active outbreaks:

```bash
curl -s "http://localhost:8000/api/map-data"
```

## Surveillance events (`SurveillanceEvent`)

List events (default `days=7`):

```bash
curl -s "http://localhost:8000/api/events"
```

Filter by source and widen time window:

```bash
curl -sG "http://localhost:8000/api/events" \
  --data-urlencode "source=promed" \
  --data-urlencode "days=30" \
  --data-urlencode "skip=0" \
  --data-urlencode "limit=50"
```

## Notes / troubleshooting

- If `/api/stats` or other endpoints error, make sure **postgres** and **redis** are healthy (Compose will wait, but first boot can take a bit).
- On startup, the backend runs `Base.metadata.create_all(...)` and tries to **seed** some initial data in a background thread. If tables exist but responses are empty, data ingestion/seed may not have populated records yet.
- For a full list of endpoints and schemas, use Swagger at `http://localhost:8000/docs`.

