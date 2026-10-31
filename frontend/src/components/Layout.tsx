import type { ReactNode } from "react";
import { Link } from "react-router";

type LayoutProps = {
  showSearch?: boolean;
  children: ReactNode;
};

export default function Layout({ showSearch = true, children }: LayoutProps) {
  return (
    <div className="layout">
      <header className="topbar">
        <Link to="/" className="logo">
          MTG Similar Cards
        </Link>
        {/* TODO(Task 5): render <SearchBar /> here when showSearch is true */}
        {showSearch ? <div className="search-slot" /> : null}
      </header>
      <main className="content">{children}</main>
      <footer className="footer">
        Card data and images via Scryfall. Magic: The Gathering is © Wizards of the Coast.
      </footer>
    </div>
  );
}
