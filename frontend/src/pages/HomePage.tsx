import { Link } from "react-router";
import Layout from "../components/Layout";
import ColorPip from "../components/ColorPip";
import SearchBar from "../components/SearchBar";
import { COLORS } from "../lib/colors";

export default function HomePage() {
  return (
    <Layout showSearch={false}>
      <section className="hero">
        <p className="eyebrow">Similar by text</p>
        <h1>Find the card you didn’t know you needed.</h1>
        <p className="lead">
          Pick any card. We read its rules text and show you every card that plays the same way, then
          narrow it down by color and type.
        </p>
        <SearchBar size="big" autoFocus />
        <p className="hero-link">
          <Link to="/search">Or build an advanced search ›</Link>
        </p>
      </section>

      <section className="band" aria-labelledby="colors-h">
        <div className="section-head">
          <h2 id="colors-h" className="section-title">Browse by color.</h2>
          <p className="lead">One tap for a fresh handful of random cards.</p>
        </div>
        <div className="pips">
          {COLORS.map((c) => (
            <ColorPip key={c} color={c} showName />
          ))}
        </div>
      </section>

      <div className="tiles">
        <section className="promo">
          <h2>Cards like this.</h2>
          <p>Open any card to see the cards whose rules text reads most alike.</p>
        </section>
        <section className="promo promo-dark">
          <h2>Advanced search.</h2>
          <p>Chain filters. Exactly what you mean.</p>
          <Link to="/search">Build a search ›</Link>
        </section>
      </div>
    </Layout>
  );
}
