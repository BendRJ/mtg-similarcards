import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router";
import App from "./App";
import { applyTheme, readStoredTheme } from "./lib/theme";
import "./styles.css";

// Before the first render, so a saved choice never flashes the system colors first.
const saved = readStoredTheme();
if (saved) applyTheme(saved);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
