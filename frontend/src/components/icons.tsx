/**
 * The app's little cartoon icons.
 *
 * Emoji render differently on every platform - Windows, macOS and Android each
 * draw their own - so these are hand-drawn instead: one flat, stroke-free set
 * in the project palette, identical everywhere, and sized in ems so they sit on
 * the text baseline wherever they are used.
 */

const YELLOW = "#F9E8A2";
const YELLOW_DEEP = "#F2D977";
const BLUE_LIGHT = "#B4E1EB";
const BLUE_MID = "#95BDD7";
const BLUE_DEEP = "#78A4CB";
const INK = "#5A6B7B";
const ORANGE = "#F2843C";
const AMBER = "#F9C74F";
const GREEN = "#7FB87D";
const PINK = "#E7A6B4";
const ROSE = "#D98B7F";
const GOLD = "#E8B84B";
const WHITE = "#FFFFFF";

const paths: Record<string, React.ReactNode> = {
  /** A streak that is still burning. */
  flame: (
    <>
      <path
        d="M12 1.5c1.1 3.9-1.1 5.3-3.3 7.3C6.2 11 4.5 13.2 4.5 15.8a7.5 7.5 0 0 0 15 0c0-3.2-1.6-5.6-3.5-7.7-1 .9-1.8 1.2-2.4.9 1-2.7.4-5.3-1.6-7.5z"
        fill={ORANGE}
      />
      <path
        d="M12.3 10.5c.7 2.3-.6 3.2-1.8 4.4-.9.9-1.5 2-1.5 3.2a3.75 3.75 0 0 0 7.5 0c0-1.8-1-3.2-2.2-4.5-.4.4-.9.6-1.3.4.5-1.3.3-2.5-.7-3.5z"
        fill={AMBER}
      />
    </>
  ),

  /** Done, ticked off. */
  check: (
    <>
      <circle cx="12" cy="12" r="10" fill={GREEN} />
      <path
        d="M7.5 12.4l3 3 6-6.4"
        fill="none"
        stroke={WHITE}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </>
  ),

  /** A milestone already passed. */
  star: (
    <path
      d="M12 3.2l2.5 5.1 5.6.8-4 3.9 1 5.6-5.1-2.7-5 2.7 1-5.6-4-3.9 5.6-.8z"
      fill={GOLD}
    />
  ),

  /** A milestone still ahead. */
  starOutline: (
    <path
      d="M12 3.2l2.5 5.1 5.6.8-4 3.9 1 5.6-5.1-2.7-5 2.7 1-5.6-4-3.9 5.6-.8z"
      fill="none"
      stroke={BLUE_MID}
      strokeWidth="1.6"
      strokeLinejoin="round"
    />
  ),

  /** The shared goal, achieved. */
  trophy: (
    <>
      <path d="M7 4h10v5.5a5 5 0 0 1-10 0z" fill={GOLD} />
      <path d="M7 5H4.5v2A3.5 3.5 0 0 0 8 10.5V8.5A1.5 1.5 0 0 1 7 7z" fill={AMBER} />
      <path
        d="M17 5h2.5v2A3.5 3.5 0 0 1 16 10.5V8.5A1.5 1.5 0 0 0 17 7z"
        fill={AMBER}
      />
      <rect x="10.8" y="14" width="2.4" height="4" fill={AMBER} />
      <rect x="7.5" y="18" width="9" height="2.6" rx="1.3" fill={GOLD} />
    </>
  ),

  /** A goal still in progress. */
  target: (
    <>
      <circle cx="12" cy="12" r="9" fill={BLUE_LIGHT} />
      <circle cx="12" cy="12" r="5.8" fill={WHITE} />
      <circle cx="12" cy="12" r="3.2" fill={BLUE_DEEP} />
      <circle cx="12" cy="12" r="1.2" fill={WHITE} />
    </>
  ),

  /** Something to celebrate together. */
  party: (
    <>
      <path d="M3.5 20.5l4.8-11 6.2 6.2z" fill={BLUE_MID} />
      <path d="M3.5 20.5l2.4-5.5 3.1 3.1z" fill={BLUE_DEEP} />
      <circle cx="17.5" cy="5.5" r="1.6" fill={PINK} />
      <circle cx="20.5" cy="10" r="1.2" fill={AMBER} />
      <circle cx="13" cy="3.5" r="1.2" fill={GREEN} />
      <circle cx="20" cy="3" r="1" fill={BLUE_DEEP} />
    </>
  ),

  /** A badge earned. */
  medal: (
    <>
      <path d="M8 2.5l2.5 6-3 1.5L5 4z" fill={BLUE_MID} />
      <path d="M16 2.5L13.5 8.5l3 1.5L19 4z" fill={BLUE_DEEP} />
      <circle cx="12" cy="15.5" r="6.5" fill={GOLD} />
      <circle cx="12" cy="15.5" r="4.4" fill={AMBER} />
      <path
        d="M12 12.4l.9 1.9 2.1.3-1.5 1.4.4 2-1.9-1-1.9 1 .4-2-1.5-1.4 2.1-.3z"
        fill={WHITE}
      />
    </>
  ),

  /** Waiting on the other side. */
  hourglass: (
    <>
      <rect x="5.5" y="2.5" width="13" height="2.4" rx="1.2" fill={BLUE_DEEP} />
      <rect x="5.5" y="19.1" width="13" height="2.4" rx="1.2" fill={BLUE_DEEP} />
      <path d="M7.5 4.9h9v2.6L12 12l4.5 4.5v2.6h-9v-2.6L12 12 7.5 7.5z" fill={BLUE_LIGHT} />
      <path d="M12 12l3.4 3.4v1.7H8.6v-1.7z" fill={AMBER} />
      <path d="M12 11.2l-1.6-1.6h3.2z" fill={AMBER} />
    </>
  ),

  /** Two ducklings side by side: the buddy pairing.
   *  Drawn chunky on purpose - this one is often rendered at 16px, where thin
   *  detail turns into mush and the ducks stop reading as ducks. */
  buddies: (
    <>
      {/* The duckling behind, in the deeper yellow. */}
      <ellipse cx="15.5" cy="16" rx="6.5" ry="5.5" fill={YELLOW_DEEP} />
      <circle cx="17" cy="8.5" r="5" fill={YELLOW_DEEP} />
      <path d="M21 7.4l2.4 1.4-2.4 1.4z" fill={ORANGE} />
      <circle cx="17.6" cy="8" r="1.3" fill={INK} />

      {/* The duckling in front. */}
      <ellipse cx="8.5" cy="17" rx="7" ry="6" fill={YELLOW} />
      <circle cx="7" cy="9" r="5.5" fill={YELLOW} />
      <path d="M3 7.9L0.6 9.3 3 10.7z" fill={ORANGE} />
      <circle cx="6.4" cy="8.4" r="1.4" fill={INK} />
    </>
  ),

  /** A streak that broke - sad, not scolding. */
  brokenStreak: (
    <>
      <path
        d="M12 1.5c1.1 3.9-1.1 5.3-3.3 7.3C6.2 11 4.5 13.2 4.5 15.8a7.5 7.5 0 0 0 15 0c0-3.2-1.6-5.6-3.5-7.7-1 .9-1.8 1.2-2.4.9 1-2.7.4-5.3-1.6-7.5z"
        fill={BLUE_MID}
      />
      <path
        d="M12.3 10.5c.7 2.3-.6 3.2-1.8 4.4-.9.9-1.5 2-1.5 3.2a3.75 3.75 0 0 0 7.5 0c0-1.8-1-3.2-2.2-4.5-.4.4-.9.6-1.3.4.5-1.3.3-2.5-.7-3.5z"
        fill={BLUE_LIGHT}
      />
      <path
        d="M20.5 4.5L4 20"
        stroke={ROSE}
        strokeWidth="2.2"
        strokeLinecap="round"
      />
    </>
  ),

  /** A request that was turned down. */
  declined: (
    <>
      <circle cx="12" cy="12" r="9.5" fill={BLUE_LIGHT} />
      <path
        d="M8 9.5h3M13 9.5h3"
        stroke={INK}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M8.5 16c1.8-1.6 5.2-1.6 7 0"
        fill="none"
        stroke={INK}
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </>
  ),

  /** Invitation sent or waiting for an answer. */
  envelope: (
    <>
      <rect x="2.5" y="5" width="19" height="14" rx="3" fill={YELLOW} />
      <path d="M2.5 8l9.5 6 9.5-6" fill="none" stroke={YELLOW_DEEP} strokeWidth="2" />
      <circle cx="18.5" cy="6.5" r="3.5" fill={ORANGE} />
      <path
        d="M17 6.5l1 1 2-2"
        fill="none"
        stroke={WHITE}
        strokeWidth="1.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </>
  ),
};

export type IconName = keyof typeof paths;

interface Props {
  name: IconName;
  size?: number | string;
  title?: string;
}

export function Icon({ name, size = "1.15em", title }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      role="img"
      aria-label={title ?? name}
      style={{ verticalAlign: "-0.18em", flexShrink: 0 }}
    >
      {paths[name]}
    </svg>
  );
}
