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
