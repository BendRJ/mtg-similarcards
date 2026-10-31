import { Route, Routes } from "react-router";
import CardPage from "./pages/CardPage";
import ColorPage from "./pages/ColorPage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import SetPage from "./pages/SetPage";

// Frontend routes are singular (/card, /set, /color); API paths are plural (/cards, /sets).
// Never add a route starting with /cards or /sets: those prefixes are proxied to the API.
export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/card/:id" element={<CardPage />} />
      <Route path="/set/:code" element={<SetPage />} />
      <Route path="/color/:c" element={<ColorPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
