# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Project Overview

Rattel is a fullstack Persian-language e-learning platform. Backend is Django 5.2 REST API, frontend is Next.js 16 (React 19) with App Router. All services run via Docker Compose.

## Commands

### Backend (`RattelBackend/`)
```bash
# Run dev server (outside Docker)
python manage.py runserver

# Migrations
python manage.py makemigrations
python manage.py migrate

# Run all tests
pytest -v

# Run a single test file
pytest tests/test_otp.py -v

# Run tests with coverage
pytest --cov
```

### Frontend (`rattel-frontend/`)
```bash
npm run dev      # dev server on :3000
npm run build    # production build
npm run lint     # eslint
```

### Docker (full stack)
```bash
docker-compose up              # start all services
docker-compose up backend      # single service
docker-compose stop            # stop all services
```

Services: `db` (Postgres :5432), `redis` (:6379), `backend` (:8000), `frontend` (:3000), `celery`, `celery-beat`, `flower` (:5555).

The backend `entrypoint.sh` runs migrations then tests (if `RUN_TESTS=1`) before starting the server.

## Architecture

### Backend Apps (`RattelBackend/`)

| App | Purpose |
|-----|---------|
| `authentication` | OTP-based registration/login flow; issues JWT |
| `users` | Profile, settings, dashboard |
| `blog` | Posts with Unicode slugs, categories, tags |
| `courses` | Course catalog, enrollment, progress |
| `cart` | Shopping cart management |
| `payment` | Zibal payment gateway integration |
| `tickets` | Support ticket system |
| `gallery` | Image gallery |
| `notifications` | Provider-based SMS (Melipayamak) and email (SMTP) dispatch |
| `siteconfig` | Site-wide settings exposed via API |
| `subscriptions` | Subscription plans (`Plan`) and per-user active subscription (`UserSubscription`) |
| `automatic_class` | Personalised memorisation plans with auto-generated steps, online call sessions, and admin call logs |

Configuration lives in `RattelBackend/RattelBackend/settings.py` and is loaded via `python-decouple` from `.env`.

### View Pattern

All views inherit `GetDataMixin` and `ResponseBuilderMixin` from `RattelBackend/mixins.py`:

- `self.get_data(request, ('field', self.validate_fn), ...)` — extracts and validates request fields; returns `(success: bool, result: dict | list[errors])`
- `self.build_response(status_code, **kwargs)` — wraps data into a DRF `Response`

### Caching (`RattelBackend/cache.py`)

Two-layer caching strategy:
1. **Backend**: `@drf_cached_response(ttl=N, cache_prefix='key')` decorator on view methods. Keys are SHA-256 hashes of view + path + data + user. User-specific invalidation is tracked separately.
2. **Frontend**: axios wrapped with `axios-cache-interceptor` (5-minute TTL on GET requests).

Cache invalidation: call `invalidate_cache('prefix')` globally or `invalidate_cache('prefix', request=request)` for one user. Models call this in their `save()` method to bust stale responses.

### Auth Flow

Registration and login are both 2-step:
1. POST credentials to `/api/v1/auth/register/` or `/api/v1/auth/login/` → starts OTP session, sends SMS
2. POST OTP to `/api/v1/auth/verify/` → returns `access` + `refresh` JWT pair

Token refresh: `/api/v1/auth/refresh/`. Tokens stored in `localStorage` on the frontend.

### Notifications

`notifications/` uses a provider pattern: `SMSHandler(provider_class, api_key)` or `EmailHandler(provider_class, ...)`. Add new providers by implementing `BaseSMSProvider` or `BaseEmailProvider`. Celery tasks dispatch notifications asynchronously when `EMAIL_USE_CELERY=True`.

### Subscription & Access Control

`subscriptions/` owns two models: `Plan` (what's for sale) and `UserSubscription` (OneToOne per user, `ends_in` date). The `Plan.add_user()` method handles purchase and extension — the payment app calls it on success.

`HasAutomaticClassAccess` permission in `automatic_class/permissions.py` checks `UserSubscription.has_feature_online_class()`. Wrap any view that requires an active subscription with this.

### automatic_class App

`AutomaticPlan.save()` auto-generates `PlanStep` rows (via `_generate_steps()`) and `OnlineCallSession` rows (via `_create_call_sessions()`, count driven by `UserSubscription.plan.online_class_limit`) the first time a plan transitions to `status=active`. This is a one-shot side effect guarded by the `_steps_generated` flag — do not re-trigger it manually.

`PlanStep.mark_delayed()` is called by the nightly Celery beat task for any pending step whose `scheduled_date` has passed.

### Frontend Architecture (`rattel-frontend/`)

Pages live in the top-level `app/` directory (Next.js App Router), not inside `src/`. Domain logic lives in `src/`:

- **`src/core/api.ts`** — single axios instance; never use raw axios elsewhere.
- **`src/core/auth/authManager.ts`** — singleton managing tokens, refresh scheduling, listeners.
- **`src/core/hooks/use*.ts`** — one hook per domain (courses, blog, cart, subscriptions, automatic class, etc.).
- **`src/core/*/Manager.ts`** — `subscriptionManager.ts`, `automaticClassManager.ts`, `authManager.ts`, etc. for imperative API calls.
- **`src/core/motionVariants.ts`** — shared Framer Motion variants; import from here instead of defining inline.

### API URL Structure

All endpoints are under `/api/v1/`:
```
/api/v1/auth/                    login, register, verify, refresh
/api/v1/users/                   profile, settings, info, dashboard
/api/v1/blog/
/api/v1/courses/
/api/v1/cart/
/api/v1/payment/
/api/v1/tickets/
/api/v1/gallery/
/api/v1/site/
/api/v1/subscriptions/plans/     public plan list
/api/v1/subscriptions/my/        authenticated user's active subscription
/api/v1/class/automatic/         automatic class (user + admin endpoints)
/api/v1/editor/upload/
```
