/**
 * The streak flame: a flat, two-tone fire drawn in the app's own palette.
 *
 * Drawn here rather than pulled from an icon pack so the project ships with no
 * third-party licence or attribution to carry, and so the flame matches the
 * ducklings - same flat, stroke-free style.
 */
export function FlameIcon({ size = 16 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      role="img"
      aria-label="streak"
      style={{ verticalAlign: "-0.15em" }}
    >
      {/* Outer flame. */}
      <path
        d="M16 2c1.5 5.2-1.4 7-4.4 9.7C8.3 14.6 6 17.6 6 21a10 10 0 0 0 20 0c0-4.3-2.1-7.4-4.6-10.2-1.3 1.2-2.4 1.6-3.2 1.2 1.3-3.6.5-7.1-2.2-10z"
        fill="#F2843C"
      />
      {/* Inner flame, brighter. */}
      <path
        d="M16.4 14c.9 3.1-.8 4.3-2.4 5.9-1.2 1.2-2 2.6-2 4.2a5 5 0 0 0 10 0c0-2.4-1.3-4.3-2.9-6-.6.6-1.2.8-1.7.6.7-1.8.4-3.3-1-4.7z"
        fill="#F9C74F"
      />
    </svg>
  );
}
