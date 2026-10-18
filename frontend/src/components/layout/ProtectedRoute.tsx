import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import { Spinner } from "../ui";

export function ProtectedRoute() {
  const location = useLocation();
  const isHydrated = useAuthStore((state) => state.isHydrated);
  const isCheckingSession = useAuthStore((state) => state.isCheckingSession);
  const user = useAuthStore((state) => state.user);

  if (!isHydrated || isCheckingSession) {
    return (
      <div className="grid min-h-screen place-items-center bg-terminal-bg">
        <Spinner label="Verificando sesion" />
      </div>
    );
  }

  if (!user) {
    return <Navigate replace state={{ from: location }} to="/login" />;
  }

  return <Outlet />;
}
