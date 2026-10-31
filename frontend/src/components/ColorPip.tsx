import { Link } from "react-router";
import type { Color } from "../lib/colors";
import { COLOR_NAMES } from "../lib/colors";

export default function ColorPip({ color, size }: { color: Color; size?: number }) {
  const style = size ? { width: size, height: size } : undefined;
  return (
    <Link
      to={`/color/${color.toLowerCase()}`}
      className={`pip pip-${color}`}
      style={style}
      aria-label={`Random ${COLOR_NAMES[color]} cards`}
    >
      {color}
    </Link>
  );
}
