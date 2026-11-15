"""Generate synthetic sales data for development and testing.

Outputs a CSV file with realistic business patterns:
- Year-over-year growth simulation
- Inflation applied to prices
- Product distribution across 5 retail categories

The thesis dataset comes from ``DatosDePrueba/ventas_fabricadas/generar_ventas.py``
(seed 2026, XLSX); this script is the CSV alternative for development. Both are
reproducible: the same seed and start date always give the same rows.

Run: python scripts/generate_dataset.py [--seed 2026] [--start 2023-11-01] [--days 1095]
"""

import argparse
import random
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

CATEGORIES = [
    "Abarrotes",
    "Limpieza",
    "Lácteos",
    "Bebidas",
    "Cuidado Personal",
]

PRODUCTS = {
    "Abarrotes": [
        "Arroz 1kg",
        "Frijol Pinto",
        "Azúcar Refinada",
        "Aceite Vegetal",
        "Lentejas",
    ],
    "Limpieza": [
        "Detergente Multiusos",
        "Cloro",
        "Escoba",
        "Jabón en polvo",
        "Desinfectante",
    ],
    "Lácteos": [
        "Leche Entera 1L",
        "Queso Panela",
        "Yogurt Natural",
        "Mantequilla",
        "Crema",
    ],
    "Bebidas": [
        "Refresco Cola 2L",
        "Agua Purificada 1L",
        "Jugo de Naranja",
        "Bebida Energética",
    ],
    "Cuidado Personal": [
        "Shampoo",
        "Pasta Dental",
        "Papel Higiénico 4 Rollos",
        "Jabón de tocador",
    ],
}

DAYS_TOTAL = 1095
YEARS_BREAKPOINTS = (365, 730)
INFLATION_FACTORS = (1.0, 1.05, 1.10)
DAILY_SALES_RANGE = [(2, 6), (4, 9), (6, 12)]
PRICE_RANGE = (15.0, 250.0)
OUTPUT_FILENAME = "ventas_3_anios_predicta.csv"
SEED = 2026
# Ends on 2026-10-30, close to the last month of the thesis dataset.
START_DATE = date(2023, 11, 1)


def _period_config(day_index: int) -> tuple[int, int, float]:
    """Return (min_sales, max_sales, inflation_factor) for a given day index."""
    for i, (breakpoint, (lo, hi), factor) in enumerate(
        zip(YEARS_BREAKPOINTS, DAILY_SALES_RANGE, INFLATION_FACTORS, strict=False)
    ):
        if day_index < breakpoint:
            return lo, hi, factor
    return DAILY_SALES_RANGE[-1][0], DAILY_SALES_RANGE[-1][1], INFLATION_FACTORS[-1]


def generate_dataset(
    days: int = DAYS_TOTAL, seed: int = SEED, start: date = START_DATE
) -> pd.DataFrame:
    """Build a synthetic sales dataframe of ``days`` days from ``start``.

    A private ``random.Random(seed)`` drives every draw, so the result depends
    only on the arguments, never on the current date or the global RNG.
    """
    rng = random.Random(seed)
    start_date = datetime(start.year, start.month, start.day)
    records: list[dict] = []

    for day_index in range(days):
        current_date = start_date + timedelta(days=day_index)
        min_sales, max_sales, inflation = _period_config(day_index)

        for _ in range(rng.randint(min_sales, max_sales)):
            category = rng.choice(CATEGORIES)
            product = rng.choice(PRODUCTS[category])
            amount = round(rng.uniform(*PRICE_RANGE) * inflation, 2)
            records.append(
                {
                    "producto": product,
                    "monto": amount,
                    "cantidad": rng.randint(1, 10),
                    "categoria": category,
                    "fecha": current_date.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    return pd.DataFrame(records)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--start", type=date.fromisoformat, default=START_DATE)
    parser.add_argument("--days", type=int, default=DAYS_TOTAL)
    args = parser.parse_args()
    print(f"Generating {args.days} days from {args.start} (seed {args.seed})...")
    df = generate_dataset(args.days, args.seed, args.start)
    output_path = Path(__file__).resolve().parent.parent / OUTPUT_FILENAME
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} records to {output_path}")


if __name__ == "__main__":
    main()
