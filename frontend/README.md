# Predicta - Frontend

> **Status:** Planning phase - implementation pending.

## Planned Stack

| Technology | Purpose |
|---|---|
| **React 18** | UI library |
| **TypeScript** | Static type checking |
| **Vite** | Build tool and dev server |
| **TailwindCSS** | Utility-first CSS framework |
| **Chart.js** | Data visualization (line, bar, mixed) |
| **TanStack Query** | Data fetching and caching |
| **React Hook Form** | Form state management |
| **Zod** | Schema validation |
| **Axios** | HTTP client with JWT interceptors |
| **Zustand** | Lightweight state management |
| **React Router** | Client-side routing |

## Planned Pages

- `Login` / `Register` - Authentication flows
- `Dashboard` - Global KPIs and main charts
- `Upload` - Drag-and-drop CSV/Excel upload
- `Analytics` - Filterable sales analytics
- `Predictions` - Forecast visualizations with confidence intervals
- `Reports` - PDF/Excel report download
- `Profile` - User account management

## Planned Structure

```
src/
├── api/           # Backend client (axios + endpoints)
├── components/    # Reusable UI components
│   ├── ui/        # Buttons, inputs, modals
│   ├── charts/    # Chart.js wrappers
│   └── layout/    # Sidebar, Navbar, ProtectedRoute
├── pages/         # Route-level pages
├── hooks/         # Custom React hooks
├── stores/        # Zustand stores
├── types/         # Shared TypeScript types
├── lib/           # Utilities (formatters, helpers)
├── App.tsx
└── main.tsx
```

## Development Setup (future)

```bash
cd frontend
npm install
npm run dev
```

The dev server will run on `http://localhost:5173` (Vite default).
