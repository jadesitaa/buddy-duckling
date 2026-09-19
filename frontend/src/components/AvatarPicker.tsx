import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { AvatarCode, AvatarOption } from "../api/types";
import { DuckAvatar } from "./DuckAvatar";

interface Props {
  value: AvatarCode;
  onChange: (code: AvatarCode) => void;
  size?: number;
}

/** The six ducklings as a radio group. The catalog comes from the API. */
export function AvatarPicker({ value, onChange, size = 64 }: Props) {
  const [options, setOptions] = useState<AvatarOption[]>([]);

  useEffect(() => {
    api
      .avatars()
      .then(setOptions)
      .catch(() => undefined);
  }, []);

  return (
    <div className="avatar-grid" role="radiogroup" aria-label="Pick your duckling">
      {options.map((option) => (
        <button
          key={option.code}
          type="button"
          role="radio"
          aria-checked={option.code === value}
          className={`avatar-option${option.code === value ? " chosen" : ""}`}
          onClick={() => onChange(option.code)}
          title={option.description}
        >
          <DuckAvatar code={option.code} size={size} title={option.title} />
          <span>{option.title.replace(" Duck", "")}</span>
        </button>
      ))}
    </div>
  );
}
