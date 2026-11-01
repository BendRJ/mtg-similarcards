import type { ReactNode } from "react";
import { Link, NavLink } from "react-router";
import SearchBar from "./SearchBar";

type LayoutProps = {
  showSearch?: boolean;
  children: ReactNode;
};

export default function Layout({ showSearch = true, children }: LayoutProps) {
  return (
    <div className="layout">
      {/* Full-width band; the inner div keeps the content at the page width. */}
      <header className="topbar">
        <nav className="topbar-inner" aria-label="Main">
          <Link to="/" className="logo">
            <span className="logo-mark" aria-hidden="true">S</span>
            MTG Similar Cards
          </Link>
          {showSearch ? (
            <div className="search-slot">
              <SearchBar />
            </div>
          ) : null}
          {/* NavLink sets aria-current="page" on its own page, which also drives the active style. */}
          <NavLink to="/search" className="nav-btn">
            Advanced search
          </NavLink>
        </nav>
      </header>
      <main className="content">{children}</main>
      <footer className="footer">
        Card data and images via Scryfall. Magic: The Gathering is © Wizards of the Coast.
      </footer>
    </div>
  );
}
