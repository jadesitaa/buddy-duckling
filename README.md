# 🐥 Buddy Duckling

[![tests](https://github.com/jadesitaa/buddy-duckling/actions/workflows/tests.yml/badge.svg)](https://github.com/jadesitaa/buddy-duckling/actions/workflows/tests.yml)

A habit tracker API with social accountability. You track your own habits, and
you pair up with a buddy: whichever side breaks their streak, the other side
hears about it. Buddies can also set a shared goal — each side has its own
target on its own habit, and the reward only unlocks once **both** sides get
there.

Built with FastAPI, PostgreSQL and async SQLAlchemy as an internship portfolio
project.

## Why it is more than CRUD

- **Streaks are timezone-aware.** Every timestamp is stored in UTC and converted
  to the user's own timezone before deciding what "today" means. Two users in
  different timezones logging at the same instant land on different days — and
  there are tests for exactly that.
- **`daily` and `weekly_n_times` habits break differently.** A daily habit
  resets on any missed day; a weekly one is judged per calendar week, so
  skipping a Tuesday costs nothing as long as the week hits its target.
- **Nothing happens automatically between users.** A partnership only carries
  notifications once it has been accepted, and notifications flow both ways.
- **Shared goals are asymmetric.** The two sides can be on completely different
  habits with different targets and finish on different days. The first one to
  finish is told they are waiting on their buddy — once.

## Tech stack

| | |
|---|---|
| API | FastAPI (async), Pydantic v2 |
| Database | PostgreSQL 17, SQLAlchemy 2 (async), Alembic |
| Auth | JWT access + refresh tokens (PyJWT), bcrypt password hashing |
| Jobs | APScheduler — hourly streak check |
| Tests | pytest, pytest-asyncio, freezegun |

## Getting started

Requirements: Python 3.12+ and Docker.

```bash
# 1. Start PostgreSQL
docker compose up -d

# 2. Install dependencies
python -m venv .venv
.venv\Scripts\activate          # Windows;  source .venv/bin/activate elsewhere
pip install -r requirements.txt

# 3. Configure
copy .env.example .env          # cp on macOS/Linux
python -c "import secrets; print(secrets.token_urlsafe(32))"   # paste as JWT_SECRET_KEY

# 4. Create the tables
alembic upgrade head

# 5. Run it
uvicorn app.main:app --reload
```

Then open <http://127.0.0.1:8000/docs> for the interactive API docs.

### Or run the whole thing in Docker

```bash
docker compose up -d --build
```

Starts PostgreSQL and the API together on <http://127.0.0.1:8000>. The container
applies the migrations itself on startup, so there is no separate setup step.
Day-to-day development is still nicer with `uvicorn --reload` on the host, with
only the database in a container.

> The database is published on host port **5433**, not the usual 5432, to stay
> out of the way of any PostgreSQL already running on the machine.

## Try it in 6 requests

1. `POST /auth/register` — create an account
2. `POST /auth/login` — get an access token, then hit **Authorize** in `/docs`
3. `POST /habits` — create a habit
4. `POST /habits/{id}/logs` — log it (an empty body means "now")
5. `POST /habits/{id}/partners` — invite a buddy by email
6. `GET /me/dashboard` — everything a home screen needs, in one request

## Running the tests

```bash
docker compose up -d      # the tests need the database
pytest
```

124 tests covering the streak rules, the ownership rules and every endpoint.
`freezegun` controls the clock, so tests about "yesterday" and "midnight in
Bangkok" give the same answer whenever they run. A separate
`buddy_duckling_test` database is created automatically and truncated between
tests.

## API

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh` |
| Profile | `GET /users/me`, `PUT /users/me` |
| Habits | `POST /habits`, `GET /habits`, `GET/PUT/DELETE /habits/{id}` |
| Logs | `POST/GET /habits/{id}/logs`, `DELETE /habits/{id}/logs/{log_id}` |
| Partners | `POST/GET /habits/{id}/partners`, `GET /me/partner-requests`, `PUT /partners/{id}/accept`, `PUT /partners/{id}/decline`, `DELETE /partners/{id}` |
| Shared goals | `POST/GET /partnerships/{id}/goals`, `DELETE /partnerships/{id}/goals/{goal_id}` |
| Badges | `GET /me/badges` |
| Notifications | `GET /me/notifications`, `GET /me/notifications/unread-count`, `PUT /notifications/{id}/read`, `PUT /me/notifications/read-all` |
| Stats | `GET /habits/{id}/stats`, `GET /me/dashboard` |

Every endpoint except `/auth/*` and `/health` requires a bearer token, and
touching something that is not yours answers **404**, never 403 — a 403 would
confirm that the id exists.

## How the code is laid out

```
app/
├── main.py          FastAPI app, routers, scheduler lifespan
├── config.py        settings from .env
├── db.py            async engine, session, declarative Base
├── deps.py          get_current_user and the shared dependencies
├── models/          SQLAlchemy tables
├── schemas/         Pydantic request/response shapes
├── routers/         HTTP layer only
├── services/        the actual rules: streaks, goals, badges, notifications
└── scheduler.py     the hourly streak check
migrations/          Alembic
tests/
```

The interesting logic lives in `services/`, kept free of HTTP and mostly free of
the database — `services/streak.py` is pure date arithmetic, which is why its
tests run in a tenth of a second.

## Background job

`app/scheduler.py` runs the streak check every hour rather than once a day: a
user's midnight depends on their timezone, so an hourly sweep is what catches
all of them. It resets broken streaks and notifies both the user and their
accepted buddies. Set `SCHEDULER_ENABLED=false` to run the API without it.

## Notifications

Notifications are stored in the database and read through the API — there is no
external provider. Everything that notifies goes through a single `notify()`
service, so adding email or push later is a one-file change.
