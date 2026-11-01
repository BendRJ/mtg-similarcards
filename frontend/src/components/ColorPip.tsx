import { Link } from "react-router";
import type { Color } from "../lib/colors";
import { COLOR_NAMES } from "../lib/colors";

type ColorPipProps = { color: Color; size?: number; showName?: boolean };

export default function ColorPip({ color, size, showName = false }: ColorPipProps) {
  const style = size ? { width: size, height: size } : undefined;
  const to = `/color/${color.toLowerCase()}`;
  const label = `Random ${COLOR_NAMES[color]} cards`;
  if (showName) {
    return (
      <Link to={to} className="pip-item" aria-label={label}>
        <span className={`pip pip-${color}`} aria-hidden="true">{color}</span>
        {COLOR_NAMES[color]}
      </Link>
    );
  }
  return (
    <Link to={to} className={`pip pip-${color}`} style={style} aria-label={label}>
      {color}
    </Link>
  );
}
