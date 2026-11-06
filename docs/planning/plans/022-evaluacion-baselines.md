# Plan 022: Evaluación honesta y modelos de referencia

## Estado

- **Estado:** TODO
- **Prioridad:** P1
- **Esfuerzo:** L
- **Riesgo:** MED
- **Depende de:** `docs/planning/plans/021-modelo-horizonte.md`
- **Categoría:** ML / tesis
- **Origen:** `docs/feedback/feedback-01.md` F-23, F-26, F-27
- **Planificado en:** commit `16cb972`, 2026-11-05

## Objetivo

Responder con evidencia a la pregunta del tribunal: "¿mejor que qué?". Evaluar
por horizonte y comparar contra modelos simples y uno más fuerte.

## Alcance

- `backend/app/ml_models/forecast.py`, `backend/app/ml_models/evaluation.py` (nuevo)
- `backend/scripts/evaluate_models.py` (nuevo)
- `backend/tests/test_ml.py`, `docs/ml-models.md`

## Pasos

1. Implementar backtesting con origen móvil y error por horizonte, con 18 meses
   iniciales de entrenamiento y horizontes de 1 a 6 meses.
   - **Verificar:** test que confirma que ningún origen ve datos futuros.
2. Implementar los modelos de referencia: último valor, mismo mes del año
   anterior y promedio móvil.
   - **Verificar:** tests con series conocidas.
3. Agregar WAPE y MASE, y una mejora porcentual frente al mejor modelo de
   referencia. Conservar R², MAPE y RMSE.
   - **Verificar:** tests con valores calculados a mano y con ventas en cero.
4. Exponer las métricas nuevas en el resultado de `monthly_forecast_series`,
   con valor nulo cuando no alcancen los datos.
   - **Verificar:** `null` nunca se convierte en cero.
5. Medir la cobertura real del intervalo de 95% en el backtest.
   - **Verificar:** el valor queda en el reporte, sea bueno o malo.
6. Agregar diagnóstico de residuos: Ljung–Box y heterocedasticidad.
   - **Verificar:** el script imprime ambas pruebas.
7. Comparar contra SARIMA o ETS solo en el script, no en runtime.
   - **Verificar:** la tabla incluye la regresión, los modelos simples y el modelo
     más fuerte.
8. Crear `evaluate_models.py` con semilla fija. Debe leer
   `DatosDePrueba/ventas_fabricadas/ventas_tienda_2_anios.xlsx` y generar las
   tablas y gráficos del capítulo.
   - **Verificar:** dos ejecuciones dan los mismos resultados.
9. Evaluar los niveles del modelo escalonado recortando el archivo a 6, 12 y 18
   meses, y comparar contra lo que ocurrió después en los datos.
   - **Verificar:** la tabla muestra el error de cada nivel. Las métricas que no
     se puedan calcular quedan nulas.
10. Documentar los resultados en `docs/ml-models.md`.
    - **Verificar:** el documento incluye también los casos donde la regresión
      pierde.

## Criterios de terminado

- Cada métrica publicada proviene de datos no vistos.
- Existe una tabla comparativa reproducible para la tesis.

## Limitaciones

Con 24 meses no se puede validar el horizonte completo de 12 meses. Dejar 12
meses de prueba deja 12 de entrenamiento, menos que los 12 coeficientes más el
intercepto del modelo. La evaluación llega hasta 6 meses. Los meses 7 a 12 son
extrapolación sin validar, y tanto la tesis como la interfaz deben decirlo.

Los datos de prueba son fabricados. Los resultados muestran que el método
funciona, pero no prueban su desempeño en una tienda real.

## STOP

- Detenerse si la regresión pierde contra el modelo estacional ingenuo en la
  mayoría de los horizontes. Es un hallazgo de la tesis: se reporta y se decide
  con el usuario. No se ajusta la evaluación para mejorar el resultado.

## Mantenimiento

Ejecutar `evaluate_models.py` cada vez que cambien las variables del modelo.
