# Comparación de costos: Predicta frente al BI privativo

Tarea 054 (P-07, PE3). Precios consultados el **2026-11-14** en las páginas oficiales
(lista abajo). Los precios cambian: revísalos antes de citarlos en la defensa.

## Supuestos

- **Escenarios** (decisión del autor): 1 usuario (el dueño), 5 usuarios (1 que diseña
  los reportes y 4 que los consultan) y 10 usuarios (1 que diseña y 9 que consultan).
- **Power BI:** Power BI Desktop es gratuito, pero publicar y compartir reportes exige
  Power BI Pro (US$14.00 por usuario al mes, pago anual). La página oficial dice
  «Upgrade to Pro or Premium to share reports»; consultar sin licencia por usuario solo
  es posible con capacidad Fabric F64 o superior (no aplica a una PyME). Se usa Pro
  para cada persona.
- **Tableau:** edición Standard (Cloud), pago anual: Creator US$75, Explorer US$42 y
  Viewer US$15 por usuario al mes. Se usa 1 Creator y el resto Viewers (la opción más
  barata).
- **Predicta:** $0 en licencias (código abierto, licencia MIT, dependencias de código
  abierto). El único costo es el hosting de `docs/despliegue.md`: Railway Hobby
  (US$5 al mes con US$5 de consumo incluidos); Vercel Hobby, Neon Free y Brevo Free
  cuestan $0. El costo no depende del número de usuarios.
- **Uso comercial:** Vercel Hobby es solo para uso personal o no comercial (Términos
  de servicio y guía de uso justo de Vercel). Una PyME que use Predicta en su negocio
  necesita Vercel Pro (asiento Developer de US$20 al mes; los asientos Viewer son
  ilimitados) u otro hosting estático cuyos términos permitan uso comercial. La fila
  «Predicta (uso comercial)» suma ese asiento.
- **Tipo de cambio:** FIX de Banco de México determinado el 13/11/2026:
  **18.5525 MXN por USD** (publicado en el DOF el 14/11/2026). Los proveedores cobran en
  USD; el costo en MXN varía con el tipo de cambio.
- No se incluyen impuestos, implementación, capacitación ni el costo del equipo.

## Costo de licencias y hosting

| Usuarios | Producto | USD al mes | USD al año | MXN al mes | MXN al año | Base |
|---|---|---|---|---|---|---|
| 1 (dueño) | Power BI Pro | 14.00 | 168.00 | 259.73 | 3,116.82 | una licencia Pro por persona para publicar y ver reportes compartidos |
| 1 (dueño) | Tableau Standard | 75.00 | 900.00 | 1,391.44 | 16,697.25 | 1 Creator |
| 1 (dueño) | Predicta (planes actuales) | 5.00 | 60.00 | 92.76 | 1,113.15 | Railway Hobby; Vercel, Neon y Brevo gratis |
| 1 (dueño) | Predicta (uso comercial) | 25.00 | 300.00 | 463.81 | 5,565.75 | Railway Hobby + 1 asiento Developer de Vercel Pro |
| 5 (1 diseña, 4 consultan) | Power BI Pro | 70.00 | 840.00 | 1,298.67 | 15,584.10 | una licencia Pro por persona para publicar y ver reportes compartidos |
| 5 (1 diseña, 4 consultan) | Tableau Standard | 135.00 | 1,620.00 | 2,504.59 | 30,055.05 | 1 Creator + Viewers |
| 5 (1 diseña, 4 consultan) | Predicta (planes actuales) | 5.00 | 60.00 | 92.76 | 1,113.15 | Railway Hobby; Vercel, Neon y Brevo gratis |
| 5 (1 diseña, 4 consultan) | Predicta (uso comercial) | 25.00 | 300.00 | 463.81 | 5,565.75 | Railway Hobby + 1 asiento Developer de Vercel Pro |
| 10 (1 diseña, 9 consultan) | Power BI Pro | 140.00 | 1,680.00 | 2,597.35 | 31,168.20 | una licencia Pro por persona para publicar y ver reportes compartidos |
| 10 (1 diseña, 9 consultan) | Tableau Standard | 210.00 | 2,520.00 | 3,896.02 | 46,752.30 | 1 Creator + Viewers |
| 10 (1 diseña, 9 consultan) | Predicta (planes actuales) | 5.00 | 60.00 | 92.76 | 1,113.15 | Railway Hobby; Vercel, Neon y Brevo gratis |
| 10 (1 diseña, 9 consultan) | Predicta (uso comercial) | 25.00 | 300.00 | 463.81 | 5,565.75 | Railway Hobby + 1 asiento Developer de Vercel Pro |

## Lectura

- Con **1 usuario**, Power BI Desktop gratuito sin publicar en la web cuesta $0; para
  consultar el tablero desde el navegador o el celular hace falta Pro (US$14 al mes).
  Predicta cuesta US$5 al mes con los planes actuales y US$25 con uso comercial.
- Con **5 usuarios**, Power BI cuesta US$70 al mes y Tableau US$135, frente a US$5–25
  de Predicta: entre 2.8 y 27 veces más.
- Con **10 usuarios**, Power BI cuesta US$140 al mes y Tableau US$210; Predicta sigue en
  US$5–25, porque su costo no crece con los usuarios.
- Límites de los planes gratuitos de Predicta: Neon Free da 1 GB de almacenamiento por
  proyecto y suspende la base tras 5 minutos sin uso (despierta en menos de un segundo);
  Brevo Free envía hasta 300 correos al día. Una PyME que los supere pasaría a planes de
  pago (Neon cobra por uso desde US$0.106 por hora de cómputo; Brevo desde US$9 al mes).

## Fuentes (consultadas el 2026-11-14)

- Power BI: https://www.microsoft.com/en-us/power-platform/products/power-bi/pricing
  («$14.00 / user/month, paid yearly»; «Upgrade to Pro or Premium to share reports»).
- Tableau: https://www.tableau.com/pricing/cloud y https://www.tableau.com/pricing/server
  («Creator: $75 per user/month, billed annually», Explorer $42, Viewer $15; Enterprise
  $115, $70 y $35). La página https://www.tableau.com/pricing/teams-orgs respondió 403.
- Vercel: https://vercel.com/pricing («Hobby is free»; «Developer seat … $20 / month»),
  https://vercel.com/legal/terms y https://vercel.com/docs/limits/fair-use-guidelines
  (uso personal o no comercial en Hobby).
- Railway: https://railway.com/pricing («Hobby — $5/month, including $5 of monthly usage
  credits»).
- Neon: https://neon.com/pricing (actualizada el 2026-11-04).
- Brevo: https://www.brevo.com/free-smtp-server/ y https://www.brevo.com/features/email-api/
  (300 correos al día en el plan gratuito; la página https://www.brevo.com/pricing/ no
  devolvió contenido).
- Tipo de cambio: FIX del 13/11/2026 según https://www.milenio.com/negocios/precio-dolar-hoy-14-noviembre-2026-mexico-a-cuanto-cotiza-en-vivo-atm
  y https://senhub.mx/herramientas/tipo-de-cambio (la página de Banxico no devolvió el
  valor; confirmarlo en https://www.banxico.org.mx antes de citarlo).
