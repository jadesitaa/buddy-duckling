import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import type { Dashboard, FrequencyType } from "../api/types";
import { DuckAvatar } from "../components/DuckAvatar";
import { FlameIcon } from "../components/FlameIcon";
import { useAuth } from "../auth/AuthContext";

function StreakLabel({
  streak,
  frequency,
}: {
  streak: number;
  frequency: FrequencyType;
}) {
  if (streak === 0) return <>No streak yet</>;
  const unit = frequency === "daily" ? "day" : "week";
  return (
    <>
      {streak} {unit}
      {streak === 1 ? "" : "s"} <FlameIcon />
    </>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loggingId, setLoggingId] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  const [newHabit, setNewHabit] = useState({
    name: "",
    frequency_type: "daily" as FrequencyType,
    frequency_target: 1,
  });

  const load = useCallback(async () => {
    try {
      setDashboard(await api.dashboard());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function logHabit(habitId: number) {
    setLoggingId(habitId);
    setError(null);
    try {
      await api.logHabit(habitId);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not log that");
    } finally {
      setLoggingId(null);
    }
  }

  async function createHabit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await api.createHabit({
        name: newHabit.name,
        frequency_type: newHabit.frequency_type,
        // A daily habit is always once a day; only weekly habits pick a number.
        frequency_target:
          newHabit.frequency_type === "daily" ? 1 : newHabit.frequency_target,
      });
      setNewHabit({ name: "", frequency_type: "daily", frequency_target: 1 });
      setAdding(false);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not add that");
    }
  }

  if (!dashboard) return <p className="muted">{error ?? "Loading…"}</p>;

  const allDone =
    dashboard.active_habits > 0 &&
    dashboard.logged_today === dashboard.active_habits;

  return (
    <div className="stack">
      <header className="spread">
        <div className="row">
          <DuckAvatar code={dashboard.avatar} size={64} />
          <div>
          <h1 style={{ marginBottom: 0 }}>Hi, {dashboard.display_name}</h1>
          <p className="muted" style={{ margin: 0 }}>
            {dashboard.today_local} · {dashboard.timezone}
          </p>
          </div>
        </div>
        <div className="row">
          <span className="pill">🏅 {dashboard.badges_earned}</span>
          <span className="pill blue">🤝 {dashboard.accepted_partnerships}</span>
        </div>
      </header>

      <section className="card spread">
        <div>
          <strong>
            {dashboard.logged_today} of {dashboard.active_habits} done today
          </strong>
          <p className="muted" style={{ margin: 0 }}>
            {allDone
              ? "Everything ticked off. Nice one!"
              : "No rush — the day is still yours."}
          </p>
        </div>
        <button onClick={() => setAdding((open) => !open)} className="secondary">
          {adding ? "Cancel" : "+ New habit"}
        </button>
      </section>

      {adding && (
        <form className="card stack" onSubmit={createHabit}>
          <label>
            <span>What do you want to keep up?</span>
            <input
              value={newHabit.name}
              onChange={(event) =>
                setNewHabit({ ...newHabit, name: event.target.value })
              }
              placeholder="Read 10 pages"
              required
              autoFocus
            />
          </label>
          <div className="row">
            <label style={{ flex: 1, marginBottom: 0 }}>
              <span>How often?</span>
              <select
                value={newHabit.frequency_type}
                onChange={(event) =>
                  setNewHabit({
                    ...newHabit,
                    frequency_type: event.target.value as FrequencyType,
                  })
                }
              >
                <option value="daily">Every day</option>
                <option value="weekly_n_times">A few times a week</option>
              </select>
            </label>
            {newHabit.frequency_type === "weekly_n_times" && (
              <label style={{ width: 130, marginBottom: 0 }}>
                <span>Times a week</span>
                <input
                  type="number"
                  min={1}
                  max={7}
                  value={newHabit.frequency_target}
                  onChange={(event) =>
                    setNewHabit({
                      ...newHabit,
                      frequency_target: Number(event.target.value),
                    })
                  }
                />
              </label>
            )}
          </div>
          <button type="submit">Add habit</button>
        </form>
      )}

      {error && <p className="error">{error}</p>}

      {dashboard.habits.length === 0 ? (
        <p className="card muted">
          No habits yet. Add your first one — one small thing is plenty.
        </p>
      ) : (
        <ul className="stack" style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {dashboard.habits.map((habit) => (
            <li key={habit.habit_id} className="card spread">
              <div>
                <strong>{habit.name}</strong>
                <p className="muted" style={{ margin: 0 }}>
                  <StreakLabel
                    streak={habit.current_streak}
                    frequency={habit.frequency_type}
                  />
                  {habit.longest_streak > habit.current_streak &&
                    ` · best ${habit.longest_streak}`}
                </p>
              </div>
              <button
                onClick={() => logHabit(habit.habit_id)}
                disabled={habit.logged_today || loggingId === habit.habit_id}
                className={habit.logged_today ? "secondary" : ""}
              >
                {habit.logged_today ? "✓ Done today" : "Mark done"}
              </button>
            </li>
          ))}
        </ul>
      )}

      <p className="muted" style={{ textAlign: "center" }}>
        Signed in as {user?.email}
      </p>
    </div>
  );
}
