import { useEffect } from "react";
import { BrowserRouter, Route, Routes, useNavigate } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { useAuthStore } from "./stores/authStore";

function UnauthorizedRedirect() {
  const navigate = useNavigate();

  useEffect(() => {
    const handleUnauthorized = () => navigate("/login", { replace: true });
    window.addEventListener("predicta:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("predicta:unauthorized", handleUnauthorized);
  }, [navigate]);

  return null;
}

function AppRoutes() {
  return (
    <>
      <UnauthorizedRedirect />
      <Routes>
        <Route element={<HomePage />} path="/" />
        <Route element={<HomePage />} path="*" />
      </Routes>
    </>
  );
}

export default function App() {
  const hydrate = useAuthStore((state) => state.hydrate);

  useEffect(() => hydrate(), [hydrate]);

  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
