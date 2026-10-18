import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";

interface AuthLayoutProps {
  title: string;
  description: string;
  children: ReactNode;
}

export function AuthLayout({ title, description, children }: AuthLayoutProps) {
  return (
    <main className="grid min-h-screen place-items-center bg-terminal-bg px-4 py-10">
      <div className="grid w-full max-w-md gap-8">
        <header className="grid gap-3 text-center">
          <NavLink className="font-mono text-sm font-semibold text-terminal-amber" to="/">
            PREDICTA / ACCESO
          </NavLink>
          <h1 className="text-3xl font-semibold text-terminal-text">{title}</h1>
          <p className="text-sm leading-6 text-terminal-muted">{description}</p>
        </header>
        {children}
      </div>
    </main>
  );
}
