# HARSH TRADER AI — Production Deployment & Observability Guide

## 1. Docker Compose Stack
The system is fully containerized across four microservices:

1. **`postgres`**: Database service (PostgreSQL 15) with volume persistence.
2. **`redis`**: Cache & task queue service (Redis 7).
3. **`backend`**: FastAPI application server (Uvicorn / Python 3.11).
4. **`frontend`**: Vite React TS static web build served via Nginx or Node.

```bash
docker-compose up --build -d
```

## 2. Environment Variables Checklist (`.env`)
- `DATABASE_URL`: PostgreSQL connection string.
- `REDIS_URL`: Redis cache URI.
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`: LLM provider API keys.
- `MARKET_DATA_PROVIDER`: Set to `MOCK`, `YFINANCE`, or `LIVE`.
- `WHATSAPP_PROVIDER`: Set to `MOCK` or `OFFICIAL`.
- `JWT_SECRET`: Secret key for JWT signing.

## 3. Observability & Health Monitoring
- Health endpoint: `GET /api/system/health`
- Returns status (`HEALTHY`, `DEGRADED`, `FAILED`), active market session state, provider status, and data quality threshold configuration.
