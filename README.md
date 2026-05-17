# CleanPlates

Institutional food waste monitoring platform with a FastAPI backend and SvelteKit dashboard frontend.

## Frontend

The Phase 9 frontend lives in `frontend/`.

```bash
cd frontend
npm install
npm run dev
```

By default Vite serves the dashboard at `http://localhost:5173` and proxies `/api`, `/ws`, `/static`, and `/health` to the FastAPI backend at `http://127.0.0.1:8000`.

Useful checks:

```bash
npm run check
npm run build
```

## Production

Phase 10 deployment artifacts are included for a single-host Docker Compose
deployment with FastAPI, ARQ, Redis, Nginx, and an optional Cloudflare Tunnel.

```bash
cp .env.prod.example .env
python scripts/deploy_preflight.py --create-dirs
docker compose -f docker-compose.prod.yml up -d --build
```

Useful hardening checks:

```bash
python scripts/verify_indexes.py
python scripts/rbac_audit.py
python scripts/load_test.py --base-url http://127.0.0.1
```

For Cloudflare Tunnel, replace the hostname and credentials in
`cloudflare/config.yml`, then start the tunnel profile:

```bash
docker compose -f docker-compose.prod.yml --profile tunnel up -d cloudflared
```
