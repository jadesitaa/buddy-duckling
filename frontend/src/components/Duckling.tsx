/** The mascot: flat, stroke-free, and slightly proud of you. */
export function Duckling({ size = 96 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      role="img"
      aria-label="A small yellow duckling"
    >
      <ellipse cx="60" cy="104" rx="34" ry="6" fill="#B4E1EB" opacity="0.5" />
      <ellipse cx="60" cy="74" rx="34" ry="28" fill="#F9E8A2" />
      <circle cx="60" cy="42" r="25" fill="#F9E8A2" />
      <ellipse cx="26" cy="76" rx="12" ry="16" fill="#F4DC85" />
      <ellipse cx="94" cy="76" rx="12" ry="16" fill="#F4DC85" />
      <circle cx="51" cy="40" r="3.5" fill="#5A6B7B" />
      <circle cx="69" cy="40" r="3.5" fill="#5A6B7B" />
      <path d="M53 50 h14 a7 7 0 0 1 -14 0 z" fill="#F2B85C" />
      <ellipse cx="51" cy="96" rx="7" ry="4" fill="#F2B85C" />
      <ellipse cx="69" cy="96" rx="7" ry="4" fill="#F2B85C" />
    </svg>
  );
}
