import { useId, type ReactNode } from "react";

export interface ChartTable {
  /** Header of the first column, e.g. "Mes". */
  rowHeader: string;
  /** One header per series. */
  columns: string[];
  rows: { label: string; values: string[] }[];
}

interface ChartFrameProps {
  /** Short name of the chart, announced as its accessible name. */
  label: string;
  /** Optional sentence with what the chart shows beyond its name. */
  description?: string;
  /** The chart's values as text, for screen readers. */
  table: ChartTable;
  className?: string;
  children: ReactNode;
}

/** Text shown for a period without sales; a missing value is never zero. */
export const NO_SALES = "Sin ventas";

/** Wraps a canvas chart as an image with a name, a description, and an equivalent data table. Every chart uses it. */
export function ChartFrame({ label, description, table, className, children }: ChartFrameProps) {
  const descriptionId = useId();
  return (
    <figure className="m-0">
      <div aria-describedby={description ? descriptionId : undefined} aria-label={label} className={className} role="img">
        {children}
      </div>
      {description && (
        <p className="sr-only" id={descriptionId}>
          {description}
        </p>
      )}
      {/* sr-only goes on a wrapper: a table ignores width: 1px and would widen the page. */}
      <div className="sr-only">
        <table>
          <caption>Datos de {label}</caption>
          <thead>
            <tr>
              <th scope="col">{table.rowHeader}</th>
              {table.columns.map((column) => (
                <th key={column} scope="col">
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row) => (
              <tr key={row.label}>
                <th scope="row">{row.label}</th>
                {row.values.map((value, index) => (
                  <td key={index}>{value}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </figure>
  );
}

/** Builds table rows from labels and one value list per series. */
export function chartTableRows(
  labels: string[],
  series: (number | null)[][],
  format: (value: number) => string,
): ChartTable["rows"] {
  return labels.map((label, index) => ({
    label,
    values: series.map((values) => {
      const value = values[index];
      return value === null || value === undefined ? NO_SALES : format(value);
    }),
  }));
}
