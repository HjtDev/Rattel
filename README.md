# Rattel

A fullstack Persian-language e-learning platform with subscription-gated features, personalised memorisation plans, and OTP-based authentication.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2 + Django REST Framework |
| Frontend | Next.js 16 (React 19, App Router) |
| Database | PostgreSQL 18 |
| Cache / Broker | Redis 8 |
| Task queue | Celery 5 + Celery Beat (DB scheduler) |
| Auth | JWT (SimpleJWT) via OTP SMS flow |
| Payments | Zibal gateway |
| Container | Docker Compose |

## Running locally

### Full stack (Docker)

```bash
docker-compose up
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1/ |
| Django Admin | http://localhost:8000/admin/ |
| Flower (Celery) | http://localhost:5555 |

Set `RUN_TESTS=1` in the `backend` service environment (already the default in `docker-compose.yml`) to run the test suite inside the container before the server starts.

### Backend only

```bash
cd RattelBackend
python manage.py migrate
python manage.py runserver
```

### Frontend only

```bash
cd rattel-frontend
npm install
npm run dev
```

## Environment

Copy `RattelBackend/.env.example` to `RattelBackend/.env` and fill in the required values (database URL, Redis URL, JWT secret, SMS API key, Zibal credentials, etc.).

The frontend reads:
- `NEXT_PUBLIC_API_URL` — public-facing backend URL (used by the browser, e.g. `http://localhost:8000`)
- `INTERNAL_API_URL` — internal Docker network URL (used by Next.js server-side, e.g. `http://backend:8000/api/v1`)

## Testing

```bash
# All backend tests
cd RattelBackend && pytest -v

# Single file
pytest tests/test_otp.py -v

# With coverage
pytest --cov
```

## Architecture overview

See [CLAUDE.md](CLAUDE.md) for a detailed breakdown of the backend app structure, view patterns, caching strategy, auth flow, subscription/access control, and frontend conventions.
