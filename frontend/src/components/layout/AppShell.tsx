import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../stores/authStore";
import { Badge, Button } from "../ui";
import { cn } from "../../lib/cn";

const navigation = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Cargar ventas", to: "/upload" },
  { label: "Predicciones", to: "/predictions" },
  { label: "Reportes", to: "/reports" },
  { label: "Perfil", to: "/profile" },
];

function Navigation({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav aria-label="Navegacion principal" className="grid gap-1">
      {navigation.map((item) => (
        <NavLink
          className={({ isActive }) =>
            cn(
              "rounded-md px-3 py-2 text-sm transition-colors",
              isActive
                ? "bg-terminal-amber/10 text-terminal-amber"
                : "text-terminal-muted hover:bg-terminal-surface hover:text-terminal-text",
            )
          }
          key={item.to}
          onClick={onNavigate}
          to={item.to}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppShell() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const clearSession = useAuthStore((state) => state.clearSession);

  function logout() {
    clearSession();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-terminal-bg text-terminal-text">
      <header className="flex min-h-16 items-center justify-between border-b border-terminal-border px-4 lg:hidden">
        <NavLink className="font-mono font-semibold text-terminal-amber" to="/dashboard">
          PREDICTA
        </NavLink>
        <Button
          aria-expanded={mobileOpen}
          aria-label="Abrir menu"
          onClick={() => setMobileOpen((open) => !open)}
          variant="ghost"
        >
          MENU
        </Button>
      </header>

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 border-r border-terminal-border bg-terminal-bg p-5",
          "lg:block",
          mobileOpen ? "block" : "hidden",
        )}
      >
        <div className="flex h-full flex-col gap-8">
          <div className="flex items-start justify-between">
            <div className="grid gap-1">
              <NavLink className="font-mono text-lg font-semibold text-terminal-amber" to="/dashboard">
                PREDICTA
              </NavLink>
              <span className="font-mono text-xs text-terminal-muted">ventas / señales</span>
            </div>
            <button
              aria-label="Cerrar menu"
              className="text-terminal-muted lg:hidden"
              onClick={() => setMobileOpen(false)}
              type="button"
            >
              X
            </button>
          </div>
          <Navigation onNavigate={() => setMobileOpen(false)} />
          <div className="mt-auto grid gap-4 border-t border-terminal-border pt-4">
            <div className="grid gap-2">
              <span className="truncate text-sm text-terminal-text">{user?.nombre_usuario}</span>
              <Badge>{user?.correo_electronico}</Badge>
            </div>
            <Button onClick={logout} variant="ghost">
              Cerrar sesion
            </Button>
          </div>
        </div>
      </aside>

      <main className="min-h-screen lg:pl-64">
        <div className="mx-auto max-w-7xl p-5 sm:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
