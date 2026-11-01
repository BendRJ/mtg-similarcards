import type { ReactNode } from "react";
import { Link, NavLink } from "react-router";
import SearchBar from "./SearchBar";
import ThemeToggle from "./ThemeToggle";

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
          <Link to="/" className="logo">Similar Cards</Link>
          {/* NavLink sets aria-current="page" on its own page, which also drives the active style. */}
          <div className="nav-links">
            <NavLink to="/" end className="nav-link">Discover</NavLink>
            <NavLink to="/search" className="nav-link">Advanced search</NavLink>
          </div>
          {showSearch ? (
            <div className="search-slot">
              <SearchBar />
            </div>
          ) : null}
          <ThemeToggle />
        </nav>
      </header>
      <main className="content">{children}</main>
      <footer className="footer">
        Card data and images via Scryfall. Magic: The Gathering is © Wizards of the Coast.
      </footer>
    </div>
  );
}
