# Predicta - Frontend

> **Status:** Implemented. Every page below consumes the FastAPI backend.

## Stack

| Technology | Purpose |
|---|---|
| **React 19** | UI library |
| **TypeScript** | Static type checking |
| **Vite** | Build tool and dev server |
| **Tailwind CSS v4** | Styling, with hand-written primitives in `src/components/ui/` |
| **Chart.js** (react-chartjs-2) | Line and bar charts, each wrapped in the accessible `ChartFrame` |
| **TanStack Query** | Server state and caching |
| **React Hook Form** + **Zod** | Forms and validation |
| **Axios** | HTTP client with the Bearer token and the 401 handler |
| **Zustand** | Session store, persisted to localStorage |
| **React Router** | Client-side routing |

## Pages

- `/` - Home
- `/login`, `/register` - Authentication
- `/dashboard` - KPIs and series in general, by category, by month, and for the whole history
- `/upload` - CSV/XLSX/SQL upload, load summary, paged history, and purge
- `/predictions` - Monthly projection with its band, saved projections, next-day forecast, and plain-language metrics
- `/reports` - Excel and PDF downloads
- `/profile` - User account

Everything except `/`, `/login`, and `/register` sits behind `ProtectedRoute` and the `AppShell` layout.

## Structure

```
src/
├── api/           # One typed client per backend area, on the shared Axios instance
├── components/
│   ├── ui/        # Buttons, inputs, modal, ChartFrame, InfoHint
│   ├── analytics/ # Dashboard charts and filters
│   ├── forecast/  # Projection chart, tables, quality
│   ├── etl/       # Upload dropzone, summary, and history table
│   ├── auth/      # Auth page layout
│   └── layout/    # AppShell, ProtectedRoute, session cache guard
├── pages/         # Route-level pages
├── stores/        # Zustand auth store
├── types/         # Types mirroring the backend schemas
├── lib/           # Formatters, transforms, validation, metric texts
├── test/          # Vitest setup
├── App.tsx
└── main.tsx
```

## Development Setup

```bash
cd frontend
npm install
npm run dev
```

The dev server runs on `http://localhost:5173`, the backend's default CORS origin.

Set `VITE_API_URL` in `.env` when the backend does not run at
`http://localhost:8000`. Run `npm run lint`, `npm run typecheck`,
`npm test -- --run`, and `npm run build` before submitting frontend changes.
