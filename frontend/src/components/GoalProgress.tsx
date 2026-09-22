import type { GoalProgressLine } from "../api/types";
import { Icon } from "./icons";

/**
 * One goal as a single line with a bar.
 *
 * Handles the three shapes a goal can take: personal with a target, personal
 * and open-ended (no bar, just a running count), and shared with a buddy
 * (the bar is the pair's joint progress, with both streaks underneath).
 */
export function GoalProgress({ goal }: { goal: GoalProgressLine }) {
  const openEnded = goal.target === null;

  return (
    <div className="goal-line">
      <div className="spread" style={{ gap: "0.5rem" }}>
        <span>
          <Icon name={goal.achieved ? "trophy" : goal.kind === "shared" ? "buddies" : "target"} />{" "}
          <strong>{goal.title}</strong>{" "}
          <span className="muted">· {goal.habit_name}</span>
        </span>
        <span className="muted">
          {openEnded
            ? `${goal.current} days so far`
            : `${goal.current} / ${goal.target} days`}
        </span>
      </div>

      {!openEnded && (
        <div className="bar">
          <div className="bar-fill" style={{ width: `${goal.percent ?? 0}%` }} />
        </div>
      )}

      {goal.kind === "shared" && (
        <p className="muted" style={{ margin: "0.15rem 0 0" }}>
          with {goal.buddy_name} · you {goal.my_streak}d, them {goal.buddy_streak}d
          {goal.my_streak !== goal.buddy_streak &&
            " — the pair moves at the slower of the two"}
        </p>
      )}

      {openEnded && (
        <p className="muted" style={{ margin: "0.15rem 0 0" }}>
          No end date — just keep the streak alive.
        </p>
      )}
    </div>
  );
}
