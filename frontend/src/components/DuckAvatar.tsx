/**
 * The six pickable ducklings, drawn flat and stroke-free.
 *
 * Each one is the same base duck with a different prop, so they read as a set
 * rather than six unrelated drawings.
 */

export type AvatarCode =
  | "clover"
  | "nerd"
  | "bow"
  | "adventurer"
  | "foodie"
  | "chill";

const BODY = "#F9E8A2";
const BODY_SHADE = "#F4DC85";
const BEAK = "#F2B85C";
const EYE = "#5A6B7B";
const BLUE = "#78A4CB";
const BLUE_LIGHT = "#B4E1EB";
const PINK = "#E7A6B4";
const GREEN = "#8CC08A";

/** Body, head, both wings, feet and eyes - shared by every duckling. */
function BaseDuck({ eyes }: { eyes?: React.ReactNode }) {
  return (
    <>
      <ellipse cx="60" cy="74" rx="34" ry="28" fill={BODY} />
      <circle cx="60" cy="42" r="25" fill={BODY} />
      {/* One wing each side, so the duck is symmetrical. */}
      <ellipse cx="26" cy="76" rx="12" ry="16" fill={BODY_SHADE} />
      <ellipse cx="94" cy="76" rx="12" ry="16" fill={BODY_SHADE} />
      {/* Everything below is mirrored around x = 60, the centre line. */}
      <ellipse cx="51" cy="96" rx="7" ry="4" fill={BEAK} />
      <ellipse cx="69" cy="96" rx="7" ry="4" fill={BEAK} />
      <path d="M53 50 h14 a7 7 0 0 1 -14 0 z" fill={BEAK} />
      {eyes ?? (
        <>
          <circle cx="51" cy="40" r="3.5" fill={EYE} />
          <circle cx="69" cy="40" r="3.5" fill={EYE} />
        </>
      )}
    </>
  );
}

const HAT = "#B08A5B";
const HAT_DARK = "#8F6E45";
const HAT_BAND = "#6F5434";
const GOLD = "#E8C87A";

/** Every prop below is centred on x = 60 so the ducks stay symmetrical. */
const ducks: Record<AvatarCode, React.ReactNode> = {
  clover: (
    <>
      <BaseDuck />
      {/* A four leaf clover growing straight up from the top of the head. */}
      <g transform="translate(60 14)">
        <rect x="-1.5" y="2" width="3" height="10" rx="1.5" fill="#6FA86D" />
        <circle cx="-7" cy="0" r="6" fill={GREEN} />
        <circle cx="7" cy="0" r="6" fill={GREEN} />
        <circle cx="0" cy="-7" r="6" fill={GREEN} />
        <circle cx="0" cy="7" r="6" fill="#7FB87D" />
        <circle cx="0" cy="0" r="2" fill="#6FA86D" />
      </g>
    </>
  ),

  nerd: (
    <>
      <BaseDuck
        eyes={
          <>
            <circle cx="51" cy="40" r="3" fill={EYE} />
            <circle cx="69" cy="40" r="3" fill={EYE} />
          </>
        }
      />
      {/* Round glasses, one lens each side of the centre line. */}
      <g fill="none" stroke={EYE} strokeWidth="2.5">
        <circle cx="51" cy="40" r="9" />
        <circle cx="69" cy="40" r="9" />
      </g>
      <rect x="58" y="38.5" width="4" height="2.5" fill={EYE} />
      {/* A book held in both wings. */}
      <g transform="translate(60 72)">
        <rect x="-14" y="-7" width="28" height="15" rx="2" fill={BLUE_LIGHT} />
        <rect x="-14" y="-7" width="28" height="4" rx="2" fill={BLUE} />
        <rect x="-1" y="-7" width="2" height="15" fill={BLUE} />
      </g>
    </>
  ),

  bow: (
    <>
      <BaseDuck />
      {/* A ribbon on top, with a loop and a tail on each side. */}
      <g transform="translate(60 16)">
        <path d="M-2 0 L-15 -8 Q-18 0 -15 8 Z" fill={PINK} />
        <path d="M2 0 L15 -8 Q18 0 15 8 Z" fill={PINK} />
        <path d="M-2 2 L-9 14 L-4 13 Z" fill="#D98FA1" />
        <path d="M2 2 L9 14 L4 13 Z" fill="#D98FA1" />
        <circle cx="0" cy="0" r="4.5" fill="#D98FA1" />
      </g>
    </>
  ),

  adventurer: (
    <>
      <BaseDuck />
      {/* A bag worn at the front, on a strap over both shoulders. */}
      <path
        d="M48 52 Q54 64 54 74 M72 52 Q66 64 66 74"
        fill="none"
        stroke={HAT_DARK}
        strokeWidth="4.5"
        strokeLinecap="round"
      />
      <g transform="translate(60 82)">
        <rect x="-15" y="-10" width="30" height="20" rx="5" fill={HAT} />
        <path d="M-15 -5 a5 5 0 0 1 5 -5 h20 a5 5 0 0 1 5 5 z" fill={HAT_DARK} />
        <rect x="-4" y="-3" width="8" height="6" rx="2" fill={GOLD} />
      </g>
      {/* A proper explorer hat: dome, band, and a curved brim. */}
      <g>
        <path d="M43 30 Q44 11 60 11 Q76 11 77 30 Z" fill={HAT} />
        <path d="M43 26 h34 v5 h-34 z" fill={HAT_BAND} />
        <path
          d="M28 31 Q60 20 92 31 Q60 41 28 31 Z"
          fill={HAT}
        />
        <path d="M28 31 Q60 37 92 31 Q60 41 28 31 Z" fill={HAT_DARK} />
      </g>
    </>
  ),

  foodie: (
    <>
      <BaseDuck />
      {/* A slice of cake on a plate, held in both wings. */}
      <g transform="translate(60 78)">
        <path d="M-11 6 L0 -10 L11 6 Z" fill="#F7D9C4" />
        <path d="M-7 0 L0 -10 L7 0 Z" fill="#E7A6B4" />
        <circle cx="0" cy="-11" r="3" fill="#D9584F" />
        <rect x="-16" y="6" width="32" height="4" rx="2" fill="white" />
      </g>
      {/* A crumb on each cheek. */}
      <circle cx="46" cy="52" r="1.6" fill="#E7A6B4" />
      <circle cx="74" cy="52" r="1.6" fill="#E7A6B4" />
    </>
  ),

  chill: (
    <>
      <BaseDuck
        eyes={
          <>
            {/* Sunglasses instead of eyes. */}
            <rect x="42" y="35" width="16" height="10" rx="4" fill={EYE} />
            <rect x="62" y="35" width="16" height="10" rx="4" fill={EYE} />
            <rect x="57" y="38" width="6" height="2.5" fill={EYE} />
          </>
        }
      />
      {/* A cold drink held in both wings. */}
      <g transform="translate(60 80)">
        <path d="M-9 -9 L9 -9 L6 11 L-6 11 Z" fill={BLUE_LIGHT} />
        <rect x="-9" y="-9" width="18" height="4" rx="2" fill="white" />
        <rect x="-1.5" y="-22" width="3" height="14" rx="1.5" fill={PINK} />
      </g>
    </>
  ),
};

interface Props {
  code: AvatarCode;
  size?: number;
  title?: string;
}

export function DuckAvatar({ code, size = 64, title }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 120 120"
      role="img"
      aria-label={title ?? `${code} duck`}
    >
      <ellipse cx="60" cy="104" rx="34" ry="6" fill={BLUE_LIGHT} opacity="0.5" />
      {ducks[code] ?? ducks.clover}
    </svg>
  );
}
