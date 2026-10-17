# Machine Learning Models

> Documentation pending - to be expanded in Phase 4 of the roadmap.

## Current approach

**Linear Regression with monthly seasonality dummies**

- Feature: `mes_indice` (sequential month index) + 12 binary month indicators
- Target: monthly aggregated sales amount
- Forecast horizon: 12 months
- Limitation: assumes linear trend, no complex non-linear patterns

## Planned improvements

- Compare with SARIMA, Prophet, and XGBoost
- Add confidence intervals to predictions
- Expose model metrics (R², MAPE, RMSE) via API
- Add per-category and per-product predictions
