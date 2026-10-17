"""Generate synthetic sales data for development and testing.

Outputs a CSV file with realistic business patterns:
- Year-over-year growth simulation
- Inflation applied to prices
- Product distribution across 5 retail categories
"""

import random
from datetime import datetime, timedelta
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


def _period_config(day_index: int) -> tuple[int, int, float]:
    """Return (min_sales, max_sales, inflation_factor) for a given day index."""
    for i, (breakpoint, (lo, hi), factor) in enumerate(
        zip(YEARS_BREAKPOINTS, DAILY_SALES_RANGE, INFLATION_FACTORS, strict=False)
    ):
        if day_index < breakpoint:
            return lo, hi, factor
    return DAILY_SALES_RANGE[-1][0], DAILY_SALES_RANGE[-1][1], INFLATION_FACTORS[-1]


def generate_dataset(days: int = DAYS_TOTAL) -> pd.DataFrame:
    """Build a synthetic sales dataframe covering the given number of days."""
    start_date = datetime.now() - timedelta(days=days)
    records: list[dict] = []

    for day_index in range(days):
        current_date = start_date + timedelta(days=day_index)
        min_sales, max_sales, inflation = _period_config(day_index)

        for _ in range(random.randint(min_sales, max_sales)):
            category = random.choice(CATEGORIES)
            product = random.choice(PRODUCTS[category])
            amount = round(random.uniform(*PRICE_RANGE) * inflation, 2)
            records.append(
                {
                    "producto": product,
                    "monto": amount,
                    "categoria": category,
                    "fecha": current_date.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    return pd.DataFrame(records)


def main() -> None:
    print(f"Generating {DAYS_TOTAL} days of synthetic sales data...")
    df = generate_dataset()
    output_path = Path(__file__).resolve().parent.parent / OUTPUT_FILENAME
    df.to_csv(output_path, index=False)
    print(f"Wrote {len(df)} records to {output_path}")


if __name__ == "__main__":
    main()
