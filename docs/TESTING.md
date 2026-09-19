# Testing guide

How Buddy Duckling is tested, and what to check when you change the parts that
are easy to get wrong: daily streaks, duration-based shared goals, and badges.

Written for anyone picking this repo up — a reviewer reading it cold, or you in
three months.

## Running the suite

```bash
docker compose up -d          # the tests need PostgreSQL
pytest                        # ~2 minutes, 147 tests
pytest tests/test_streak_service.py    # ~0.2s, pure logic, run this constantly
pytest -k "milestone or duration"      # one slice
pytest -x -q                           # stop at the first failure
```

CI runs the same two commands on every push (`.github/workflows/tests.yml`),
plus `alembic upgrade head` so a broken or missing migration fails the build.

## The shape of the suite

| Layer | Files | What it proves | Speed |
|---|---|---|---|
| **Unit** | `test_streak_service.py` | The date arithmetic itself: consecutive days, missed days, weeks, local-day conversion, longest run | ~0.2s, no I/O |
| **Integration** | `test_auth`, `test_habits`, `test_habit_logs`, `test_partnerships`, `test_shared_goals`, `test_badges`, `test_notifications`, `test_profile`, `test_stats` | Real HTTP through the real app against a real PostgreSQL: status codes, ownership, persistence | ~2s per file |
| **Job** | `test_streak_check.py` | The hourly sweep: who gets reset, who gets told | ~15s |

The split is deliberate. Streak rules are the most delicate thing in the
project, so they are tested twice: once as pure functions where every edge case
is cheap to write, and once through the API where the timezone conversion,
the database round-trip and the notification side effects all take part.

### Fixtures worth knowing (`tests/conftest.py`)

- `engine` — builds the schema once per session. It does **not** drop and
  recreate per test: doing that hands PostgreSQL new ids for the enum types
  while asyncpg still caches the old ones, which fails with
  `cache lookup failed for type ...`.
- `db` — truncates every table before each test and re-seeds the badge rows
  that migration `862ce56f3f67` normally inserts.
- `client` — an `AsyncClient` bound to the app with `get_db` overridden.
- `auth_client` — already registered and signed in as `duckling@example.com`.
- `make_user("someone@example.com")` — a second (third, fourth) signed-in
  client. Every ownership test uses this: *the other person must not be able
  to see or touch this.*

### Controlling time

Anything that depends on "today" freezes the clock:

```python
@pytest.fixture(autouse=True)
def frozen_now():
    with freeze_time("2026-03-10T12:00:00Z"):   # Tuesday, 19:00 in Bangkok
        yield
```

Two rules learned the hard way:

1. **Freeze before the fixtures run**, not inside the test body. Tokens are
   issued with the clock in force when `auth_client` is built; if the test then
   jumps time forward, the token is already expired and every call gets a 401.
2. **Jump time only around the code under test.** Move HTTP calls back outside
   the nested `freeze_time` block, or read them back before the jump.

## Streak edge cases

The rules live in `app/services/streak.py`. What the tests pin down:

| Case | Expected | Where |
|---|---|---|
| N days in a row | streak = N | `test_n_consecutive_days_build_a_streak_of_n` |
| Logged yesterday, not yet today | streak survives — the day is not over | `test_a_streak_survives_until_the_end_of_the_next_day` |
| Last log two days ago | streak = 0 | `test_a_missed_day_resets_the_streak_to_zero` |
| Old long run, fresh run today | only the run touching today counts | `test_only_the_run_touching_today_counts` |
| Twice on the same local day | counts once, second call is a 409 | `test_logging_the_same_day_twice_is_rejected` |
| 16:59:59Z vs 17:00:00Z in Bangkok | different local days → streak of 2 | `test_midnight_local_time_counts_as_the_new_day` |
| Same instant, Bangkok vs London | different `log_date_local` | `test_a_users_timezone_decides_their_local_day` |
| `weekly_n_times`, days skipped | streak intact if the week hit its target | `test_weekly_habit_is_not_reset_by_a_missed_day` |
| Current week unfinished | never breaks the streak — the week is still running | `test_an_unfinished_current_week_does_not_break_the_streak` |
| Backfilled logs | `longest_streak` recomputed from the whole history | `test_it_remembers_a_run_that_already_ended` |
| Log deleted | both streaks recomputed | `test_deleting_a_log_recalculates_the_streak` |

**When you touch streak code, add a case here first.** The bug this caught
already: `longest_streak = max(longest, current)` silently lost records when a
user backfilled a missed day, because `current` was 0 at that moment.

### The daily job

`run_daily_streak_check` is called directly in tests rather than through
APScheduler — schedulers are not worth waiting for in a test suite. Cases:
a live streak is untouched; a streak logged yesterday is not reset; two idle
days resets it and notifies; **running twice notifies once**; an accepted buddy
is told, a pending one is not; the buddy who accepted can break their own streak
and warn the inviter; inactive habits are skipped; and two users in different
timezones are judged against their own midnight.

## Duration-based shared goals

A goal now carries `duration_days` — the joint commitment — alongside each
side's own `target_streak_a` / `target_streak_b`.

**The rule to keep straight:** joint progress is `min(streak_a, streak_b)`. The
pair moves at the pace of whoever is behind, while each side's *own* target
decides when that side is personally done.

| Case | Expected | Where |
|---|---|---|
| Targets omitted | both default to `duration_days` | `test_duration_sets_both_targets_when_none_are_given` |
| A at 4, B at 2, duration 4 | joint 2, 50%, 2 days remaining | `test_joint_progress_moves_at_the_pace_of_whoever_is_behind` |
| Both at 2 of 4 | 25% and 50% milestones reached, 75%/100% not | `test_milestones_flip_as_the_pair_moves` |
| Both finished | `achieved_at` set, 100%, 0 remaining, every milestone reached | `test_a_finished_duration_goal_is_fully_marked` |
| Both far past the target | capped at 100%, never negative days | `test_progress_never_runs_past_one_hundred_percent` |
| `duration_days = 1` | milestones round to 1 day, none reached at zero | `test_a_one_day_duration_still_has_sane_milestones` |
| `duration_days = 0` | 422 | `test_duration_must_be_at_least_one_day` |
| One side finishes first | that side alone is notified, **once** | `test_waiting_is_only_announced_once` |
| Different habit types | daily side and weekly side both count | `test_the_two_sides_can_be_on_different_habit_types` |

Rounding is the trap here: `round(duration * percent / 100)` can produce 0 for
short goals, and a 0-day milestone would read as "reached" before anyone has
done anything. `milestones_for` clamps to a minimum of 1 — keep that test.

### Personal rewards

Each side promises itself something, and neither side can write the other's:

- the creator's reward lands on their own side (`my_side` says which)
- the buddy's `PUT .../my-reward` changes only `personal_reward_b`
- a stranger gets a 404, not a 403
- the "you're waiting on your buddy" notification quotes the personal reward;
  the "achieved" notification quotes the shared one

## Badges

Awarded in `app/services/badges.py` on every successful log.

| Case | Expected | Where |
|---|---|---|
| Streak below the first milestone | no badge | `test_no_badges_before_the_first_milestone` |
| Streak hits 3 | `streak_3` + one notification | `test_three_day_streak_earns_the_first_badge` |
| Keep logging past 3 | no duplicate | `test_a_badge_is_never_awarded_twice_for_the_same_habit` |
| Streak reaches 7 | both `streak_3` and `streak_7` | `test_a_week_long_streak_earns_both_milestones` |
| Second habit hits 3 | same badge, earned again on that habit | `test_the_same_badge_can_be_earned_on_a_second_habit` |
| Someone else's badges | invisible | `test_badges_are_private_to_their_owner` |

Two deliberate design points, both load-bearing:

1. The check is `milestone_days <= current_streak`, **not** `==`. A backfilled
   log can jump a streak from 5 to 10 and must not skip the 7-day badge.
2. `UNIQUE(user_id, badge_id, habit_id)` is the real guarantee. The service
   also checks, but the constraint is what holds under concurrent requests.

## Profile and avatars

Avatars are a closed set, which is itself the security property: no uploads, no
file storage, nothing one user can put in front of another. Tests cover the
public catalog endpoint, the default duck for new users, picking one at
sign-up, partial updates leaving other fields alone, a rejected unknown value
(422, stored value untouched), and a buddy seeing the right avatar on a
partnership.

## Writing a new test

1. **Name it as a sentence.** `test_a_missed_day_resets_the_streak` beats
   `test_streak_2`. The failure output is then a readable claim.
2. **Assert on content, not just shape.** `assert len(items) == 1` once passed
   against a 401 error body, because `{"detail": ...}` also has length 1.
3. **Cover the refusal too.** Every feature gets a "someone else tries it" test;
   the expected answer is 404, never 403.
4. **Put pure logic in `services/`** so it can be tested without HTTP, and keep
   the router thin.

## Gaps worth filling next

- **Concurrency:** two simultaneous logs for the same habit and day. The unique
  constraint should make one a 409; nothing proves it today.
- **DST:** a user in a timezone that shifts (`Europe/London` in March) crossing
  the change. The code uses `zoneinfo` and should be right, but it is untested.
- **Frontend:** no automated tests yet. The natural first step is Vitest plus
  Testing Library on `api/client.ts` (token refresh and replay) and the
  progress maths in `GoalList`.
- **Load:** `describe_all` and the buddies page issue one query per habit. Fine
  for a portfolio, worth a join before it meets real data.
