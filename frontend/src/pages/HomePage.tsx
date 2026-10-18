import { Link } from "react-router-dom";
import { Badge, Card } from "../components/ui";
import { cn } from "../lib/cn";

const actionLink = "inline-flex min-h-10 items-center justify-center rounded-md px-4 py-2 text-sm font-semibold transition-colors";

export function HomePage() {
  return (
    <main className="mx-auto grid min-h-screen max-w-6xl content-center gap-8 px-6 py-12 lg:grid-cols-[1.2fr_0.8fr]">
      <section className="grid content-center gap-6">
        <Badge tone="warning">Predicta / sistema listo</Badge>
        <div className="grid gap-4">
          <p className="font-mono text-sm text-terminal-amber">ventas // señales // decisiones</p>
          <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-terminal-text sm:text-7xl">
            Tus ventas, con siguiente movimiento.
          </h1>
          <p className="max-w-xl text-lg leading-8 text-terminal-muted">
            Plataforma de análisis para pequeñas empresas. Carga tu historial y convierte datos en decisiones claras.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link className={cn(actionLink, "bg-terminal-amber text-terminal-bg hover:bg-amber-300")} to="/login">
            Entrar al panel
          </Link>
          <Link className={cn(actionLink, "border border-terminal-border bg-terminal-surface text-terminal-text hover:border-terminal-amber")} to="/register">
            Crear cuenta
          </Link>
        </div>
      </section>
      <Card className="grid content-center gap-5">
        <div className="flex items-center justify-between border-b border-terminal-border pb-4">
          <span className="font-mono text-xs text-terminal-muted">PREDICTA / READY</span>
          <span className="size-2 rounded-full bg-terminal-positive" />
        </div>
        <div className="grid gap-2">
          <span className="text-sm text-terminal-muted">Ingresos proyectados</span>
          <strong className="font-mono text-4xl text-terminal-amber">$--,--</strong>
        </div>
        <div className="grid gap-2 border-t border-terminal-border pt-4 text-sm text-terminal-muted">
          <span>Sube un archivo para activar tus métricas.</span>
          <Link className="text-terminal-amber hover:underline" to="/upload">
            Cargar ventas
          </Link>
          <span className="font-mono text-terminal-positive">estado: esperando datos</span>
        </div>
      </Card>
    </main>
  );
}
