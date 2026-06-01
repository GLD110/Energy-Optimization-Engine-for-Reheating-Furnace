# Energy Optimization Engine for Reheating Furnace

A full-stack application for monitoring, optimizing, and reporting energy use in a multi-zone steel reheating furnace. The backend combines constrained optimization (SciPy SLSQP), ML heating-curve prediction (LSTM with heuristic fallback), and CO₂ estimation; the React dashboard exposes live state, analytics, and what-if scenarios.

## Features

| Area | Description |
|------|-------------|
| **Live furnace** | Simulated multi-zone temperatures, fuel flow, conveyor speed, and anomaly flags |
| **Heating curve** | ML/heuristic slab temperature trajectory and recommended zone setpoints |
| **Energy optimization** | Fuel and zone setpoint recommendations under exit-temperature constraints |
| **CO₂ & ESG** | Emissions summary, efficiency score, and historical trend |
| **Recommendations** | Rule-based operational suggestions from live state |
| **What-if** | Compare baseline vs. adjusted fuel and conveyor speed |

## Architecture

```
┌─────────────────────┐     /api (proxy)      ┌──────────────────────────┐
│  React + Vite       │ ────────────────────► │  FastAPI (Python)        │
│  (port 5173)        │                       │  (port 8000)             │
└─────────────────────┘                       │  • optimization_engine   │
                                              │  • live_simulator        │
                                              │  • emissions / anomaly   │
                                              │  • SQLite (aiosqlite)    │
                                              └───────────┬──────────────┘
                                                          │
                                              ┌───────────▼──────────────┐
                                              │  ml/ (LSTM, XGB, heur.)  │
                                              └──────────────────────────┘
```

## Project structure

```
.
├── backend/
│   ├── app/              # FastAPI app, routes, services, DB models
│   ├── ml/               # LSTM training, predictor, artifacts
│   ├── scripts/          # smoke_api.py
│   └── requirements.txt
└── frontend/
    └── src/              # React pages and API client
```

## Prerequisites

- **Python** 3.10+ (3.11 recommended)
- **Node.js** 18+ and npm
- Optional: CUDA-capable GPU for faster LSTM training (CPU works)

## Quick start

### 1. Backend

From the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Health check: `GET /api/v1/health`

### 2. Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). Vite proxies `/api` to the backend on port 8000.

### 3. Demo data (optional)

Seed historical sensor and emissions rows for charts:

```http
POST http://127.0.0.1:8000/api/v1/ingest/demo-batch
```

Or use the interactive docs at `/docs`.

## Configuration

Create `backend/.env` to override defaults (see `backend/app/config.py`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./furnace.db` | Async SQLAlchemy URL |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Allowed frontend origins |
| `ML_ARTIFACT_PATH` | `ml/artifacts/lstm_curve.pt` | Trained LSTM checkpoint |

## API overview

All routes are under `/api/v1`:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health |
| `GET` | `/live` | Current furnace state |
| `POST` | `/predict/heating-curve` | Slab heating curve and setpoints |
| `POST` | `/optimize` | Constrained fuel/zone optimization |
| `GET` | `/emissions/summary` | Current CO₂ and efficiency |
| `GET` | `/emissions/trend` | Time series (`window_hours`, default 168) |
| `GET` | `/recommendations` | Operational recommendations |
| `POST` | `/whatif` | Fuel/conveyor scenario comparison |
| `POST` | `/ingest/demo-batch` | Seed demo time-series data |

## ML model (optional)

Heating-curve prediction uses a trained LSTM when `ml/artifacts/lstm_curve.pt` exists; otherwise a physics-inspired heuristic is used.

Train and write the artifact:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m ml.train_lstm
```

## Smoke test

With the virtual environment active and dependencies installed:

```powershell
cd backend
python scripts/smoke_api.py
```

Exercises health, heating-curve prediction, and optimization endpoints via FastAPI’s test client (no running server required).

## Production build

```powershell
# Frontend static assets
cd frontend
npm run build

# Backend (example)
cd ..\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Serve `frontend/dist` behind your reverse proxy or configure the API separately; point the frontend at the API base URL if not using the Vite dev proxy.

## License

Proprietary / internal use — add your organization’s license terms here if applicable.
