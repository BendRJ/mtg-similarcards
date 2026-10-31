import Layout from "../components/Layout";
import ColorPip from "../components/ColorPip";
import SearchBar from "../components/SearchBar";
import { COLORS } from "../lib/colors";

export default function HomePage() {
  return (
    <Layout showSearch={false}>
      <div className="hero">
        <div className="logo">⟡ Similar Cards</div>
        <SearchBar size="big" autoFocus />
        <div className="pips">
          {COLORS.map((c) => (
            <ColorPip key={c} color={c} />
          ))}
        </div>
      </div>
    </Layout>
  );
}
