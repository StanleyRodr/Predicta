import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ForecastMetricCard } from "./ForecastMetricCard";
import { ForecastQuality } from "./ForecastQuality";

describe("forecast components", () => {
  it("shows separate amount and interval values", () => {
    render(<ForecastMetricCard interval={{ inferior: 80, superior: 120 }} label="Monto predicho" value={100} />);

    expect(screen.getByText("Monto predicho")).toBeInTheDocument();
    expect(screen.getByText(/80/)).toBeInTheDocument();
    expect(screen.getByText(/120/)).toBeInTheDocument();
  });

  it("does not represent null metrics as zero", () => {
    render(
      <ForecastQuality
        amount={{ r2: null, mape: null, rmse: null }}
        quantity={{ r2: 0.8, mape: 2, rmse: 1 }}
      />,
    );

    expect(screen.getAllByText("No disponible")).toHaveLength(3);
    expect(screen.getByText("0.80")).toBeInTheDocument();
  });
});
