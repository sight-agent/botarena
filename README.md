# botarena (MVP scaffold)

Monorepo:

- `backend/`: FastAPI + SQLAlchemy + Alembic + JWT auth + bots/versions API
- `frontend/`: Vite + React + TypeScript SPA

See `SPEC.md` for the full product spec (sandbox execution / ranked / matches are intentionally stubbed in this scaffold).

## Local dev

### Backend + Postgres (Docker)

```bash
docker compose up --build
```

Backend will be available at `http://localhost:8000`:

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/bots` (auth)
- `POST /api/bots` (auth)
- `GET /api/bots/{bot_id}` (auth)
- `POST /api/bots/{bot_id}/versions` (auth)
- `POST /api/bots/{bot_id}/active_version` (auth)

### Frontend (dev server)

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at `http://localhost:5173` and will call the backend at `http://localhost:8000` by default.

To point the frontend to a different backend:

```bash
VITE_API_BASE="http://localhost:8000" npm run dev
```

## Tests

### Backend

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
pytest -q
```

### Frontend

```bash
cd frontend
npm ci
npm run test:ci
npm run build
```

## CI / Deploy

- GitHub Actions CI runs backend pytest and frontend test/build on pushes and PRs.
- GitHub Pages workflow deploys the frontend build from `main`.

