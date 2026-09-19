import { useCallback, useEffect, useState } from "react";

import { api } from "../api/client";
import type { SharedGoal } from "../api/types";

function SideProgress({
  label,
  value,
  target,
  done,
}: {
  label: string;
  value: number;
  target: number;
  done: boolean;
}) {
  const percent = Math.min(100, Math.round((value / target) * 100));
  return (
    <div style={{ flex: 1, minWidth: 140 }}>
      <span className="muted">
        {done ? "✅ " : ""}
        {label}
      </span>
      <div className="bar">
        <div className="bar-fill" style={{ width: `${percent}%` }} />
      </div>
      <span className="muted">
        {value} / {target} days
      </span>
    </div>
  );
}

/** The joint bar, with a tick for every quarter of the commitment. */
function JointProgress({ goal }: { goal: SharedGoal }) {
  return (
    <div>
      <div className="spread" style={{ marginBottom: "0.25rem" }}>
        <strong>
          Together: {goal.joint_days} of {goal.duration_days} days
        </strong>
        <span className="muted">
          {goal.achieved_at
            ? "Done!"
            : `${goal.days_remaining} to go · ${goal.joint_percent}%`}
        </span>
      </div>
      <div className="bar joint">
        <div className="bar-fill" style={{ width: `${goal.joint_percent}%` }} />
        {goal.milestones.slice(0, -1).map((milestone) => (
          <span
            key={milestone.percent}
            className={`tick${milestone.reached ? " reached" : ""}`}
            style={{ left: `${milestone.percent}%` }}
          />
        ))}
      </div>
      <div className="row" style={{ gap: "0.4rem", flexWrap: "wrap" }}>
        {goal.milestones.map((milestone) => (
          <span
            key={milestone.percent}
            className={`pill milestone${milestone.reached ? " reached" : ""}`}
          >
            {milestone.reached ? "★" : "☆"} {milestone.percent}% · {milestone.days}d
          </span>
        ))}
      </div>
    </div>
  );
}

interface Props {
  title: string;
  yourLabel: string;
  buddyLabel: string;
  partnershipId: number;
  paired: boolean;
  onChange: () => void;
}

export function GoalList({
  title,
  yourLabel,
  buddyLabel,
  partnershipId,
  paired,
  onChange,
}: Props) {
  const [goals, setGoals] = useState<SharedGoal[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [form, setForm] = useState({
    title: "",
    reward_description: "",
    duration_days: 7,
    sameTargets: true,
    target_streak_a: 7,
    target_streak_b: 7,
  });

  const load = useCallback(async () => {
    try {
      setGoals(await api.goals(partnershipId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load goals");
    }
  }, [partnershipId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function create(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await api.createGoal(partnershipId, {
        title: form.title,
        reward_description: form.reward_description || null,
        duration_days: form.duration_days,
        // Left out, the API gives both sides the joint duration as a target.
        target_streak_a: form.sameTargets ? null : form.target_streak_a,
        target_streak_b: form.sameTargets ? null : form.target_streak_b,
      });
      setForm({ ...form, title: "", reward_description: "" });
      setAdding(false);
      await load();
      onChange();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not add that goal");
    }
  }

  return (
    <div className="stack" style={{ gap: "0.8rem" }}>
      <div className="spread">
        <strong>{title}</strong>
        {paired && (
          <button className="secondary" onClick={() => setAdding((open) => !open)}>
            {adding ? "Cancel" : "+ New goal"}
          </button>
        )}
      </div>

      {goals.map((goal) => (
        <article key={goal.id} className="card soft stack" style={{ gap: "0.6rem" }}>
          <div className="spread">
            <div>
              <strong>
                {goal.achieved_at ? "🏆 " : "🎯 "}
                {goal.title}
              </strong>
              {goal.reward_description && (
                <p className="muted" style={{ margin: 0 }}>
                  🎉 When you both finish: {goal.reward_description}
                </p>
              )}
            </div>
            <button
              className="ghost"
              onClick={async () => {
                await api.deleteGoal(partnershipId, goal.id);
                await load();
                onChange();
              }}
            >
              Remove
            </button>
          </div>

          <JointProgress goal={goal} />

          <div className="row" style={{ alignItems: "flex-start", gap: "1.5rem" }}>
            <SideProgress
              label={goal.my_side === "a" ? `You · ${yourLabel}` : buddyLabel}
              value={goal.current_streak_a}
              target={goal.target_streak_a}
              done={goal.reached_a}
            />
            <SideProgress
              label={goal.my_side === "b" ? `You · ${yourLabel}` : buddyLabel}
              value={goal.current_streak_b}
              target={goal.target_streak_b}
              done={goal.reached_b}
            />
          </div>

          {goal.achieved_at && (
            <p className="notice" style={{ margin: 0 }}>
              Unlocked! You both kept it up for {goal.duration_days} days — time to
              go do it together 🎉
            </p>
          )}
        </article>
      ))}

      {error && <p className="error">{error}</p>}

      {!paired && (
        <p className="muted" style={{ margin: 0 }}>
          Your buddy needs to pair a habit of their own before you can set a
          shared goal.
        </p>
      )}

      {paired && goals.length === 0 && !adding && (
        <p className="muted" style={{ margin: 0 }}>
          No shared goal yet. Pick something you both keep up for a set number of
          days, and something to go do together once you get there.
        </p>
      )}

      {adding && (
        <form className="card soft stack" onSubmit={create} style={{ gap: "0.6rem" }}>
          <label style={{ marginBottom: 0 }}>
            <span>What are you both going for?</span>
            <input
              placeholder="Two weeks of reading"
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              required
              autoFocus
            />
          </label>
          <div className="row" style={{ flexWrap: "wrap" }}>
            <label style={{ marginBottom: 0, flex: "1 1 130px" }}>
              <span>Keep it up for (days)</span>
              <input
                type="number"
                min={1}
                max={365}
                value={form.duration_days}
                onChange={(event) =>
                  setForm({
                    ...form,
                    duration_days: Number(event.target.value),
                    target_streak_a: Number(event.target.value),
                    target_streak_b: Number(event.target.value),
                  })
                }
              />
            </label>
            <label style={{ marginBottom: 0, flex: "1 1 220px" }}>
              <span>What will you do together afterwards?</span>
              <input
                placeholder="Go get ice cream together"
                value={form.reward_description}
                onChange={(event) =>
                  setForm({ ...form, reward_description: event.target.value })
                }
              />
            </label>
          </div>

          <label className="row" style={{ marginBottom: 0, gap: "0.5rem" }}>
            <input
              type="checkbox"
              checked={form.sameTargets}
              onChange={(event) =>
                setForm({ ...form, sameTargets: event.target.checked })
              }
              style={{ width: "auto" }}
            />
            <span style={{ margin: 0 }}>
              Same target for both of us ({form.duration_days} days)
            </span>
          </label>

          {!form.sameTargets && (
            <div className="row" style={{ flexWrap: "wrap" }}>
              <label style={{ marginBottom: 0, flex: "1 1 120px" }}>
                <span>Target · side A</span>
                <input
                  type="number"
                  min={1}
                  max={365}
                  value={form.target_streak_a}
                  onChange={(event) =>
                    setForm({ ...form, target_streak_a: Number(event.target.value) })
                  }
                />
              </label>
              <label style={{ marginBottom: 0, flex: "1 1 120px" }}>
                <span>Target · side B</span>
                <input
                  type="number"
                  min={1}
                  max={365}
                  value={form.target_streak_b}
                  onChange={(event) =>
                    setForm({ ...form, target_streak_b: Number(event.target.value) })
                  }
                />
              </label>
            </div>
          )}

          <button type="submit">Set this goal</button>
        </form>
      )}
    </div>
  );
}
