# Buddy Duckling

Habit tracker API with social accountability, built as an internship portfolio project.

## Concept

Users track personal habits and pair up with an accountability "buddy". The pairing
is bidirectional: whichever side breaks their streak, the other side gets notified via
LINE Notify. Buddies can also set a shared goal — each side has their own streak target
(possibly on a different habit), and once both sides hit their own target, a shared
reward (e.g. "get ice cream together") unlocks for both.

## Tech stack

- FastAPI (async)
- PostgreSQL + SQLAlchemy (async ORM) + Alembic for migrations
- Pydantic v2 for validation/schemas
- JWT authentication (python-jose or fastapi-users)
- pytest + freezegun for mocking time in tests
- LINE Notify API via httpx
- APScheduler for the daily streak-check job

## Database schema

1. **users**: id, email (unique), password_hash, display_name, timezone (e.g. "Asia/Bangkok"),
   line_notify_token (nullable), created_at, updated_at
2. **habits**: id, user_id (FK), name, description, frequency_type (enum: daily,
   weekly_n_times), frequency_target (int), current_streak (int, default 0),
   longest_streak (int, default 0), is_active (bool, default true), created_at, updated_at
3. **habit_logs**: id, habit_id (FK), logged_at_utc (timestamp), log_date_local (date),
   created_at, UNIQUE(habit_id, log_date_local)
4. **accountability_partners**: id, habit_id (FK), partner_habit_id (FK, nullable),
   partner_user_id (FK), status (enum: pending/accepted/declined), created_at,
   UNIQUE(habit_id, partner_user_id)
5. **shared_goals**: id, partnership_id (FK -> accountability_partners),
   target_streak_a (int), target_streak_b (int), title, reward_description,
   achieved_at (nullable), created_at
6. **badges**: id, code (unique, e.g. "streak_7"), title, milestone_days (int)
7. **user_badges**: id, user_id (FK), badge_id (FK), habit_id (FK), earned_at,
   UNIQUE(user_id, badge_id, habit_id)

## Core logic rules

- **Streak calculation**: always convert timestamps to the user's timezone before
  deciding what "today" is — never reason about streaks in raw UTC. `daily` habits
  reset to 0 on any missed day; `weekly_n_times` habits are checked per calendar week,
  not per day. Recalculate `current_streak`/`longest_streak` on log insert, not on read.
- **Accountability partner**: no auto-linking — a partnership only sends notifications
  once `status = accepted`. Notifications are bidirectional: either side breaking their
  streak notifies the other side. A daily APScheduler job checks all habits for broken
  streaks and fires LINE Notify.
- **Shared goals**: compare each side's own `current_streak` against their own target
  (`target_streak_a` / `target_streak_b`) — the two sides can be on completely different
  habits and reach their target on different days. `achieved_at` is set only once both
  sides have independently reached their own target. Notify the first side to finish that
  they're waiting on their partner; notify both once the goal is fully achieved.
- **Badges**: on every successful log, check whether `current_streak` matches any
  badge's `milestone_days`; if so and the user hasn't already earned that badge for that
  habit, insert a `user_badges` row.
- **Ownership**: every endpoint except `/auth/*` must check the JWT and that the
  requester owns the resource, or is an accepted partner on it.

## API endpoints

- `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`
- `GET/PUT /users/me`
- `POST/GET /habits`, `GET/PUT/DELETE /habits/{id}`
- `POST/GET /habits/{id}/logs`, `DELETE /habits/{id}/logs/{log_id}`
- `POST/GET /habits/{id}/partners`, `PUT /partners/{id}/accept`,
  `PUT /partners/{id}/decline`, `DELETE /partners/{id}`
- `GET /me/partner-requests`
- `POST/GET /partnerships/{id}/goals`, `DELETE /partnerships/{id}/goals/{id}`
- `GET /habits/{id}/stats`, `GET /me/dashboard`
- `GET /me/badges`

## Testing expectations

pytest coverage must include, at minimum:
- N consecutive days building a streak correctly
- A missed day resetting the streak to 0
- Logging exactly at midnight local time being counted on the correct day
- A user timezone that differs from UTC producing the correct "local day"
- `weekly_n_times` habits not being reset the same way `daily` habits are

Use `freezegun` to control the current time in tests rather than relying on real time
passing.

## Git conventions

Use Conventional Commits, one logical change per commit:

```
feat: add JWT authentication endpoints
fix: correct timezone conversion in streak calculation
test: add tests for weekly_n_times streak logic
docs: add setup instructions to README
chore: setup Alembic migration config
refactor: extract streak logic into separate service
```

Commit in this rough order: scaffold → auth → habits CRUD → habit logs + streak logic
(with tests alongside, not after) → accountability partners → shared goals → badges →
docs. Avoid vague messages like "fix bug" or "update code".

## Branding (for an optional frontend/landing page)

- Mascot: a flat-design duckling, stroke-free (no outlines), simple and cute
- Palette: `#F9E8A2` (soft yellow), `#B4E1EB` (very light blue), `#95BDD7` (mid blue),
  `#78A4CB` (deeper blue)
- Mood: notebook / ruled-paper feel, calm and low-pressure — not a guilt-driven tracker
