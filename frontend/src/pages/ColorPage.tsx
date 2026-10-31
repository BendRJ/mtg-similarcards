import { useParams } from "react-router";
import { api } from "../api";
import CardGrid from "../components/CardGrid";
import ErrorState from "../components/ErrorState";
import ColorPip from "../components/ColorPip";
import Layout from "../components/Layout";
import Loading from "../components/Loading";
import { COLOR_NAMES, parseColor } from "../lib/colors";
import type { Color } from "../lib/colors";
import { useAsync } from "../lib/useAsync";
import NotFoundPage from "./NotFoundPage";

export default function ColorPage() {
  const { c = "" } = useParams();
  const color = parseColor(c);
  if (color === null) return <NotFoundPage />;
  return <ColorCards color={color} />;
}

function ColorCards({ color }: { color: Color }) {
  const title = `Random ${COLOR_NAMES[color]} cards`;
  const { status, data, error, reload } = useAsync((s) => api.random([color], 100, s), [color]);
  document.title = title;
  return (
    <Layout>
      <div className="toolbar">
        <ColorPip color={color} size={34} />
        <h1>{title}</h1>
        <button type="button" className="btn" onClick={reload}>
          Shuffle
        </button>
      </div>
      {status === "loading" && <Loading />}
      {status === "error" && error && <ErrorState error={error} onRetry={reload} />}
      {status === "ok" && data && <CardGrid cards={data} />}
    </Layout>
  );
}
