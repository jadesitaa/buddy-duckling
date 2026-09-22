import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import type { Dashboard, FrequencyType } from "../api/types";
import { DuckAvatar } from "../components/DuckAvatar";
import { GoalProgress } from "../components/GoalProgress";
import { Icon } from "../components/icons";
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
      {streak === 1 ? "" : "s"} <Icon name="flame" />
    </>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loggingId, setLoggingId] = useState<number | null>(null);
  const [adding, setAdding] = useState(false);
  // Which habit currently has its "new goal" form open, if any.
  const [goalFor, setGoalFor] = useState<number | null>(null);
  const [goalForm, setGoalForm] = useState({ title: "", days: "" });
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

  async function createGoal(event: React.FormEvent, habitId: number) {
    event.preventDefault();
    setError(null);
    try {
      await api.createPersonalGoal(habitId, {
        title: goalForm.title,
        // Blank means an open-ended goal: track the streak, never finish.
        target_days: goalForm.days ? Number(goalForm.days) : null,
      });
      setGoalForm({ title: "", days: "" });
      setGoalFor(null);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not add that goal");
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
          <span className="pill" title="badges earned">
            <Icon name="medal" size="1em" /> {dashboard.badges_earned}
          </span>
          <span className="pill blue" title="buddies">
            <Icon name="buddies" size="1em" /> {dashboard.accepted_partnerships}
          </span>
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
            <li key={habit.habit_id} className="card stack">
              <div className="spread">
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
                <div className="row">
                  <button
                    className="ghost"
                    onClick={() =>
                      setGoalFor(goalFor === habit.habit_id ? null : habit.habit_id)
                    }
                  >
                    {goalFor === habit.habit_id ? "Cancel" : "+ Goal"}
                  </button>
                  <button
                    onClick={() => logHabit(habit.habit_id)}
                    disabled={habit.logged_today || loggingId === habit.habit_id}
                    className={habit.logged_today ? "secondary" : ""}
                  >
                    {habit.logged_today ? (
                      <>
                        <Icon name="check" size="1em" /> Done today
                      </>
                    ) : (
                      "Mark done"
                    )}
                  </button>
                </div>
              </div>

              {goalFor === habit.habit_id && (
                <form
                  className="row"
                  style={{ flexWrap: "wrap" }}
                  onSubmit={(event) => createGoal(event, habit.habit_id)}
                >
                  <input
                    placeholder="Goal, e.g. Read every day this month"
                    value={goalForm.title}
                    onChange={(event) =>
                      setGoalForm({ ...goalForm, title: event.target.value })
                    }
                    style={{ flex: "1 1 200px" }}
                    required
                    autoFocus
                  />
                  <input
                    type="number"
                    min={1}
                    max={365}
                    placeholder="Days (optional)"
                    value={goalForm.days}
                    onChange={(event) =>
                      setGoalForm({ ...goalForm, days: event.target.value })
                    }
                    style={{ flex: "0 1 150px" }}
                  />
                  <button type="submit">Set goal</button>
                </form>
              )}
            </li>
          ))}
        </ul>
      )}

      {dashboard.goals.length > 0 && (
        <section className="card stack">
          <div className="spread">
            <strong>Your goals</strong>
            <span className="muted">
              {dashboard.goals.filter((goal) => goal.achieved).length} of{" "}
              {dashboard.goals.length} done
            </span>
          </div>
          {dashboard.goals.map((goal, index) => (
            <GoalProgress key={`${goal.kind}-${index}`} goal={goal} />
          ))}
        </section>
      )}

      <p className="muted" style={{ textAlign: "center" }}>
        Signed in as {user?.email}
      </p>
    </div>
  );
}
