import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { applyTheme, currentTheme, readStoredTheme } from "../lib/theme";
import ThemeToggle from "./ThemeToggle";

function prefersDark(dark: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({ matches: dark && q === "(prefers-color-scheme: dark)" }));
}

afterEach(() => {
  localStorage.clear();
  delete document.documentElement.dataset.theme;
});

describe("theme", () => {
  it("follows the system when nothing is stored", () => {
    prefersDark(true);
    expect(currentTheme()).toBe("dark");
    prefersDark(false);
    expect(currentTheme()).toBe("light");
  });

  it("prefers the stored choice and ignores junk", () => {
    prefersDark(false);
    localStorage.setItem("theme", "dark");
    expect(currentTheme()).toBe("dark");
    localStorage.setItem("theme", "purple");
    expect(readStoredTheme()).toBeNull();
  });

  it("applyTheme sets the attribute the stylesheet reads", () => {
    applyTheme("dark");
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});

describe("ThemeToggle", () => {
  it("switches light to dark and back, and remembers the choice", async () => {
    prefersDark(false);
    render(<ThemeToggle />);
    await userEvent.click(screen.getByRole("button", { name: "Switch to dark mode" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(currentTheme()).toBe("dark");
    await userEvent.click(screen.getByRole("button", { name: "Switch to light mode" }));
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(currentTheme()).toBe("light");
  });

  it("remembers only a choice that differs from the system, so picking the system theme goes back to automatic", async () => {
    prefersDark(false);
    render(<ThemeToggle />);
    await userEvent.click(screen.getByRole("button", { name: "Switch to dark mode" }));
    expect(readStoredTheme()).toBe("dark");
    await userEvent.click(screen.getByRole("button", { name: "Switch to light mode" }));
    expect(readStoredTheme()).toBeNull();
  });

  it("works when storage is blocked", async () => {
    prefersDark(false);
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new Error("blocked"); });
    render(<ThemeToggle />);
    await userEvent.click(screen.getByRole("button", { name: "Switch to dark mode" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
