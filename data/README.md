# Data Directory

This directory contains generated datasets for development and testing.

## Generating synthetic data

The dataset generator is located at `backend/scripts/generate_dataset.py`.

```bash
make seed
# or
cd backend && python scripts/generate_dataset.py
```

## Files in this directory

Generated CSV files (`.csv`) are **gitignored** because they are reproducible outputs of the generator script. Only this README and `.gitkeep` are tracked.

## Available datasets

The generator can produce:
- **1-year dataset** (365 days) - for quick smoke tests
- **3-year dataset** (1095 days, default) - for production-like training

Generated data includes realistic business patterns:
- Year-over-year growth simulation
- Inflation factor applied to prices
- Product distribution across 5 categories (Abarrotes, Limpieza, Lácteos, Bebidas, Cuidado Personal)

## Loading data into the database

After generating, upload the CSV via the API:

```bash
curl -X POST "http://localhost:8000/etl/upload-ventas" \
  -H "Authorization: Bearer <your-jwt>" \
  -F "file=@./ventas_3_anios_predicta.csv"
```

Or use the Swagger UI at `http://localhost:8000/docs`.
