import { Card } from "../components/ui";

interface SectionPlaceholderProps {
  eyebrow: string;
  title: string;
  description: string;
}

export function SectionPlaceholder({ eyebrow, title, description }: SectionPlaceholderProps) {
  return (
    <div className="grid gap-8">
      <header className="grid gap-2">
        <p className="font-mono text-sm text-terminal-amber">{eyebrow}</p>
        <h1 className="text-3xl font-semibold">{title}</h1>
        <p className="text-terminal-muted">{description}</p>
      </header>
      <Card>
        <p className="font-mono text-sm text-terminal-muted">modulo en preparacion // siguiente fase</p>
      </Card>
    </div>
  );
}
