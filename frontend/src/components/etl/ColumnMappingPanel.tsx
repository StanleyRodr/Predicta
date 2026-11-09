import type { ColumnAnalysis, ColumnMapping, ColumnRole } from "../../types/etl";
import { selectClass } from "../analytics/CategoryProductFilter";
import { Badge } from "../ui";

export const COLUMN_ROLES: { role: ColumnRole; label: string }[] = [
  { role: "producto", label: "Producto" },
  { role: "categoria", label: "Categoría" },
  { role: "monto", label: "Monto" },
  { role: "precio_unitario", label: "Precio unitario" },
  { role: "cantidad", label: "Cantidad" },
  { role: "fecha", label: "Fecha" },
];

const ORIGIN_BADGES = {
  exacto: { label: "Exacto", tone: "positive" },
  sinonimo: { label: "Sinónimo", tone: "neutral" },
} as const;

/** The server proposal as an editable mapping. */
export function mappingFromAnalysis(analysis: ColumnAnalysis): ColumnMapping {
  const mapping: ColumnMapping = {};
  for (const { role } of COLUMN_ROLES) {
    const column = analysis.propuesta[role]?.columna;
    if (column) mapping[role] = column;
  }
  return mapping;
}

/** Why the mapping cannot be loaded yet, or null when it is complete. */
export function mappingProblem(mapping: ColumnMapping): string | null {
  const used = new Set<string>();
  for (const { role } of COLUMN_ROLES) {
    const column = mapping[role];
    if (!column) continue;
    if (used.has(column)) return `La columna ${column} está asignada a dos roles.`;
    used.add(column);
  }
  const missing = [
    !mapping.producto && "Producto",
    !mapping.monto && !mapping.precio_unitario && "Monto o Precio unitario",
    !mapping.fecha && "Fecha",
  ].filter(Boolean);
  return missing.length ? `Falta asignar: ${missing.join(", ")}.` : null;
}

interface ColumnMappingPanelProps {
  analysis: ColumnAnalysis;
  value: ColumnMapping;
  onChange: (value: ColumnMapping) => void;
}

/** One select per role, preloaded with the proposal, plus a sample of the file. */
export function ColumnMappingPanel({ analysis, value, onChange }: ColumnMappingPanelProps) {
  const roleByColumn = new Map(
    COLUMN_ROLES.filter(({ role }) => value[role]).map(({ role, label }) => [value[role] as string, label]),
  );

  function change(role: ColumnRole, column: string) {
    const next = { ...value };
    if (column) next[role] = column;
    else delete next[role];
    onChange(next);
  }

  return (
    <div aria-label="Mapeo de columnas" className="grid gap-4" role="group">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {COLUMN_ROLES.map(({ role, label }) => {
          const proposal = analysis.propuesta[role];
          const origin = proposal?.origen && proposal.columna === value[role] ? ORIGIN_BADGES[proposal.origen] : null;
          return (
            <div className="grid gap-1" key={role}>
              <label className="flex flex-wrap items-center gap-2 text-sm text-terminal-muted">
                {label}
                <select
                  aria-label={`Columna para ${label}`}
                  className={selectClass}
                  onChange={(event) => change(role, event.target.value)}
                  value={value[role] ?? ""}
                >
                  <option value="">Sin asignar</option>
                  {analysis.columnas.map((column) => (
                    <option key={column} value={column}>
                      {column}
                    </option>
                  ))}
                </select>
                {origin && <Badge tone={origin.tone}>{origin.label}</Badge>}
              </label>
              {proposal && proposal.candidatos.length > 0 && !value[role] && (
                <p className="text-xs text-terminal-amber">Hay varias columnas posibles: {proposal.candidatos.join(", ")}</p>
              )}
            </div>
          );
        })}
      </div>
      {analysis.muestra.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <caption className="sr-only">Muestra del archivo</caption>
            <thead className="text-terminal-muted">
              <tr>
                {analysis.columnas.map((column) => (
                  <th className="px-2 py-1 font-medium" key={column} scope="col">
                    {roleByColumn.get(column) ?? column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {analysis.muestra.map((row, index) => (
                <tr className="border-t border-terminal-border" key={index}>
                  {analysis.columnas.map((column) => (
                    <td className="px-2 py-1 font-mono text-terminal-text" key={column}>
                      {row[column] ?? ""}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
