import { useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { getCurrentUser } from "./api/auth";
import { AppShell, ProtectedRoute } from "./components/layout";
import { Spinner } from "./components/ui";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { ProfilePage } from "./pages/ProfilePage";
import { RegisterPage } from "./pages/RegisterPage";
import { SectionPlaceholder } from "./pages/SectionPlaceholder";
import { UploadPage } from "./pages/UploadPage";
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

function SessionBootstrap() {
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const token = useAuthStore((state) => state.token);
  const setUser = useAuthStore((state) => state.setUser);
  const clearSession = useAuthStore((state) => state.clearSession);

  useEffect(() => {
    if (!isHydrated || !token) return;
    let active = true;
    getCurrentUser()
      .then((user) => {
        if (active) setUser(user);
      })
      .catch(() => {
        if (active) clearSession();
      });
    return () => {
      active = false;
    };
  }, [clearSession, isHydrated, setUser, token]);

  return null;
}

function AppRoutes() {
  return (
    <>
      <SessionBootstrap />
      <UnauthorizedRedirect />
      <Routes>
        <Route element={<HomePage />} path="/" />
        <Route element={<LoginPage />} path="/login" />
        <Route element={<RegisterPage />} path="/register" />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route element={<SectionPlaceholder description="Resumen de tu operacion." eyebrow="dashboard // resumen" title="Dashboard" />} path="/dashboard" />
            <Route element={<UploadPage />} path="/upload" />
            <Route element={<SectionPlaceholder description="Consulta monto, cantidad e intervalos." eyebrow="ml // proyeccion" title="Predicciones" />} path="/predictions" />
            <Route element={<SectionPlaceholder description="Descarga reportes de tu operacion." eyebrow="salidas // reportes" title="Reportes" />} path="/reports" />
            <Route element={<ProfilePage />} path="/profile" />
          </Route>
        </Route>
        <Route element={<Navigate replace to="/" />} path="*" />
      </Routes>
    </>
  );
}

export default function App() {
  const hydrate = useAuthStore((state) => state.hydrate);

  useEffect(() => hydrate(), [hydrate]);

  const isHydrated = useAuthStore((state) => state.isHydrated);
  if (!isHydrated) {
    return (
      <div className="grid min-h-screen place-items-center bg-terminal-bg">
        <Spinner label="Iniciando Predicta" />
      </div>
    );
  }

  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  );
}
