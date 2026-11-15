"""Generate two years of realistic, non-linear retail sales as an XLSX upload file.

Patterns simulated: weekday/weekend rhythm, payday spikes, monthly and
holiday seasonality, per-category seasonality, a non-linear growth curve with
a mid-period slump and recovery, gradual inflation, random shocks, and
closed days. Output columns match the ETL contract:
producto, monto (line total), cantidad, categoria, fecha.

Run: python generar_ventas.py  (seeded, reproducible)
"""

from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2026
START = date(2024, 11, 1)
END = date(2026, 10, 31)
BASE_TICKETS_PER_DAY = 32
OUTPUT = Path(__file__).resolve().parent / "ventas_tienda_2_anios.xlsx"

# (product, base unit price, typical max quantity)
CATALOG: dict[str, list[tuple[str, float, int]]] = {
    "Abarrotes": [
        ("Arroz 1kg", 28.0, 5),
        ("Frijol Pinto 1kg", 34.0, 4),
        ("Azúcar Refinada 1kg", 30.0, 4),
        ("Aceite Vegetal 1L", 45.0, 3),
        ("Lentejas 500g", 22.0, 3),
        ("Pasta Spaghetti 500g", 16.0, 6),
        ("Atún en lata", 24.0, 6),
        ("Harina de Trigo 1kg", 26.0, 3),
    ],
    "Limpieza": [
        ("Detergente Multiusos 1L", 38.0, 3),
        ("Cloro 1L", 18.0, 3),
        ("Escoba", 65.0, 1),
        ("Jabón en polvo 1kg", 52.0, 2),
        ("Desinfectante 1L", 42.0, 2),
        ("Esponjas (3 pzas)", 20.0, 2),
    ],
    "Lácteos": [
        ("Leche Entera 1L", 27.0, 6),
        ("Queso Panela 400g", 68.0, 2),
        ("Yogurt Natural 1L", 35.0, 3),
        ("Mantequilla 90g", 25.0, 2),
        ("Crema 200ml", 22.0, 2),
    ],
    "Bebidas": [
        ("Refresco Cola 2L", 38.0, 4),
        ("Agua Purificada 1L", 12.0, 8),
        ("Jugo de Naranja 1L", 30.0, 3),
        ("Bebida Energética", 35.0, 3),
        ("Cerveza (six pack)", 110.0, 2),
    ],
    "Cuidado Personal": [
        ("Shampoo 400ml", 72.0, 2),
        ("Pasta Dental", 32.0, 3),
        ("Papel Higiénico 4 Rollos", 40.0, 3),
        ("Jabón de tocador", 15.0, 4),
        ("Desodorante", 58.0, 2),
    ],
}

CATEGORY_WEIGHTS = {
    "Abarrotes": 0.32,
    "Bebidas": 0.24,
    "Lácteos": 0.18,
    "Limpieza": 0.14,
    "Cuidado Personal": 0.12,
}

# Weekday multiplier (Mon..Sun): weekend shopping is heavier.
WEEKDAY_FACTOR = [0.85, 0.82, 0.90, 0.95, 1.12, 1.35, 1.15]

# Month multiplier for overall traffic (Jan..Dec).
MONTH_FACTOR = [0.80, 0.84, 0.95, 1.00, 1.08, 1.02, 1.05, 1.07, 0.98, 1.00, 1.10, 1.38]

# Category-specific seasonality (Jan..Dec); unspecified = 1.0.
CATEGORY_MONTH_FACTOR = {
    "Bebidas": [0.80, 0.85, 1.00, 1.20, 1.40, 1.35, 1.25, 1.20, 1.05, 0.95, 0.90, 1.30],
    "Limpieza": [1.25, 1.00, 1.05, 1.00, 0.95, 0.95, 1.00, 1.10, 1.00, 0.95, 1.00, 1.20],
    "Cuidado Personal": [0.95, 1.00, 1.00, 1.00, 1.15, 1.00, 1.00, 1.15, 1.00, 1.00, 1.05, 1.25],
}

# Special dates: (month, day) -> traffic multiplier; 0 means closed.
SPECIAL_DAYS = {
    (1, 1): 0.0,
    (12, 25): 0.0,
    (12, 24): 1.9,
    (12, 31): 1.8,
    (12, 23): 1.6,
    (2, 14): 1.25,
    (5, 10): 1.45,
    (9, 15): 1.5,
    (9, 16): 0.6,
    (11, 2): 1.2,
}


def growth_curve(t: float) -> float:
    """Non-linear business trajectory over t in [0, 1].

    Logistic ramp-up as the store gains customers, a slump around months
    13-16 (new competitor opens nearby), then partial recovery.
    """
    ramp = 0.75 + 0.45 / (1 + np.exp(-10 * (t - 0.25)))
    slump = 1 - 0.22 * np.exp(-(((t - 0.6) / 0.07) ** 2))
    return float(ramp * slump)


def inflation(t: float) -> float:
    """Accumulated price inflation: ~4.5% per year with a faster second half."""
    return 1.0 + 0.035 * t * 2 + 0.03 * max(0.0, t - 0.5) * 2


def payday_factor(d: date) -> float:
    """Spikes on and just after the 15th and the month's end (quincena)."""
    last_day = (date(d.year + (d.month == 12), d.month % 12 + 1, 1) - timedelta(days=1)).day
    if d.day in (15, 16) or d.day in (last_day, 1):
        return 1.30
    if d.day in (17, 2):
        return 1.12
    if d.day in (12, 13, 14, 27, 28):
        return 0.90
    return 1.0


def black_friday(d: date) -> bool:
    """Fourth Friday... approximated by the 'Buen Fin' weekend (mid-November)."""
    return d.month == 11 and 14 <= d.day <= 17


def build_sales(seed: int = SEED) -> pd.DataFrame:
    """Every sale line of the two years, sorted by time; the same seed gives the same rows."""
    rng = np.random.default_rng(seed)
    total_days = (END - START).days + 1
    categories = list(CATEGORY_WEIGHTS)
    base_weights = np.array([CATEGORY_WEIGHTS[c] for c in categories])

    # A slowly drifting random walk adds week-to-week noise that is not white.
    drift = np.cumsum(rng.normal(0, 0.012, total_days))
    drift -= np.linspace(drift[0], drift[-1], total_days)

    # Unexpected shocks: rainy weeks, supply problems, local events.
    shocks = np.ones(total_days)
    for _ in range(9):
        start = rng.integers(0, total_days - 7)
        length = rng.integers(2, 8)
        shocks[start : start + length] *= rng.uniform(0.6, 1.35)

    records = []
    for i in range(total_days):
        d = START + timedelta(days=i)
        t = i / (total_days - 1)

        special = SPECIAL_DAYS.get((d.month, d.day), 1.0)
        if special == 0.0:
            continue

        traffic = (
            BASE_TICKETS_PER_DAY
            * growth_curve(t)
            * WEEKDAY_FACTOR[d.weekday()]
            * MONTH_FACTOR[d.month - 1]
            * payday_factor(d)
            * special
            * (1.4 if black_friday(d) else 1.0)
            * shocks[i]
            * np.exp(drift[i])
        )
        n_lines = int(rng.poisson(max(traffic, 1)))

        weights = base_weights * np.array(
            [CATEGORY_MONTH_FACTOR.get(c, [1.0] * 12)[d.month - 1] for c in categories]
        )
        weights /= weights.sum()
        price_level = inflation(t)
        promo_month = d.month in (3, 7) and d.day <= 7  # occasional promotions

        for _ in range(n_lines):
            category = categories[rng.choice(len(categories), p=weights)]
            product, base_price, max_qty = CATALOG[category][
                rng.integers(len(CATALOG[category]))
            ]
            qty = int(min(max_qty * 2, 1 + rng.poisson(max_qty / 3)))
            if special > 1.3 or black_friday(d):
                qty += int(rng.integers(0, 2))
            unit = base_price * price_level * rng.uniform(0.97, 1.03)
            if promo_month and category in ("Abarrotes", "Limpieza"):
                unit *= 0.88
            hour = int(rng.choice(range(8, 22), p=_HOUR_P))
            ts = datetime(d.year, d.month, d.day, hour, int(rng.integers(60)), int(rng.integers(60)))
            records.append(
                {
                    "producto": product,
                    "monto": round(unit * qty, 2),
                    "cantidad": qty,
                    "categoria": category,
                    "fecha": ts.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    return pd.DataFrame(records).sort_values("fecha", kind="stable").reset_index(drop=True)


def main() -> None:
    df = build_sales()
    df.to_excel(OUTPUT, index=False, sheet_name="ventas")
    print(f"{len(df)} filas, {df['monto'].sum():,.2f} en ventas -> {OUTPUT}")


# Store hours 8:00-21:59 with lunch and evening peaks.
_hours = np.array([0.5, 0.7, 0.9, 1.0, 1.3, 1.4, 1.1, 0.9, 1.0, 1.3, 1.5, 1.4, 1.0, 0.6])
_HOUR_P = _hours / _hours.sum()

if __name__ == "__main__":
    main()
