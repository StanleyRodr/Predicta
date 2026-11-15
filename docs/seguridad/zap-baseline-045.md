# ZAP baseline - Predicta (tarea 045, dominios reales)

Escaneo pasivo del 2026-11-14 contra `https://predicta-three-zeta.vercel.app`
(frontend en Vercel) y `https://predicta-api.up.railway.app` (API en Railway),
con ZAP 2.17.0 y su automation framework: `requestor` sobre las rutas públicas,
`spider` en cada dominio y `passiveScan-wait`. Sin escaneo activo.

## Comparación con la 039

| Alerta de la 039 | Hallazgo | Ahora |
|---|---|---|
| CSP Header Not Set (10038) | S-10 | Ya no aparece: CSP en el `<meta>` del build y en la cabecera de Vercel |
| Missing Anti-clickjacking Header (10020) | S-10 | Ya no aparece: `frame-ancestors 'none'` y `X-Frame-Options: DENY` |
| X-Content-Type-Options Header Missing (10021) | S-10 | Ya no aparece, ni en el frontend ni en la API |
| Application Error Disclosure (90022) | S-21 | Ya no aparece: `GET /` responde 200 |

## Clasificación de las alertas nuevas

| Alerta | Riesgo | Clasificación |
|---|---|---|
| Cross-Domain Misconfiguration (10098) | Medio | Riesgo aceptado (S-27). Vercel envía `Access-Control-Allow-Origin: *` en los archivos estáticos del frontend. Esos archivos son públicos, no llevan datos de usuario y no hay cookies: el token vive en `localStorage` y solo viaja a la API, que tiene su propio CORS cerrado al dominio de Vercel. Otro sitio puede leer el HTML y el JS, igual que cualquier visitante. |
| CSP: Header & Meta (10055) | Informativa | Esperado: la política va en el `<meta>` y en la cabecera, iguales salvo `frame-ancestors` (test `src/test/csp.test.ts`). |
| Information Disclosure - Suspicious Comments (10027) | Informativa | Falso positivo: `DB` dentro del código minificado de React (`createElementNS`). |
| Modern Web Application (10109) | Informativa | Esperado: es una SPA. |
| Re-examine Cache-control Directives (10015) | Informativa | Esperado en el frontend estático. Las rutas privadas de la API responden `Cache-Control: no-store`. |
| Retrieved from Cache (10050) | Informativa | Esperado: la CDN de Vercel sirve los archivos estáticos. |

## Informe de ZAP

ZAP by [Checkmarx](https://checkmarx.com/).


## Summary of Alerts

| Risk Level | Number of Alerts |
| --- | --- |
| High | 0 |
| Medium | 1 |
| Low | 0 |
| Informational | 5 |




## Insights

| Level | Reason | Site | Description | Statistic |
| --- | --- | --- | --- | --- |
| Low | Warning |  | ZAP errors logged - see the zap.log file for details | 2    |
| Low | Warning |  | ZAP warnings logged - see the zap.log file for details | 2    |
| Info | Informational | https://predicta-api.up.railway.app | Percentage of responses with status code 2xx | 44 % |
| Info | Informational | https://predicta-api.up.railway.app | Percentage of responses with status code 4xx | 55 % |
| Info | Informational | https://predicta-api.up.railway.app | Percentage of endpoints with content type application/json | 100 % |
| Info | Informational | https://predicta-api.up.railway.app | Percentage of endpoints with method GET | 100 % |
| Info | Informational | https://predicta-api.up.railway.app | Count of total endpoints | 10    |
| Info | Informational | https://predicta-api.up.railway.app | Percentage of slow responses | 72 % |
| Info | Informational | https://predicta-three-zeta.vercel.app | Percentage of responses with status code 2xx | 100 % |
| Info | Informational | https://predicta-three-zeta.vercel.app | Percentage of endpoints with content type application/javascript | 14 % |
| Info | Informational | https://predicta-three-zeta.vercel.app | Percentage of endpoints with content type text/css | 14 % |
| Info | Informational | https://predicta-three-zeta.vercel.app | Percentage of endpoints with content type text/html | 71 % |
| Info | Informational | https://predicta-three-zeta.vercel.app | Percentage of endpoints with method GET | 100 % |
| Info | Informational | https://predicta-three-zeta.vercel.app | Count of total endpoints | 7    |
| Info | Informational | https://predicta-three-zeta.vercel.app | Percentage of slow responses | 58 % |




## Alerts

| Name | Risk Level | Number of Instances |
| --- | --- | --- |
| Cross-Domain Misconfiguration | Medium | Systemic |
| CSP: Header & Meta | Informational | Systemic |
| Information Disclosure - Suspicious Comments | Informational | 1 |
| Modern Web Application | Informational | Systemic |
| Re-examine Cache-control Directives | Informational | Systemic |
| Retrieved from Cache | Informational | Systemic |




## Alert Detail



### [ Cross-Domain Misconfiguration ](https://www.zaproxy.org/docs/alerts/10098/)



##### Medium (Medium)

### Description

Web browser data loading may be possible, due to a Cross Origin Resource Sharing (CORS) misconfiguration on the web server.

* URL: https://predicta-three-zeta.vercel.app
  * Node Name: `https://predicta-three-zeta.vercel.app`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Access-Control-Allow-Origin: *`
  * Other Info: `The CORS misconfiguration on the web server permits cross-domain read requests from arbitrary third party domains, using unauthenticated APIs on this domain. Web browser implementations do not permit arbitrary third parties to read the response from authenticated APIs, however. This reduces the risk somewhat. This misconfiguration could be used by an attacker to access data that is available in an unauthenticated manner, but which uses some other form of security, such as IP address white-listing.`
* URL: https://predicta-three-zeta.vercel.app/
  * Node Name: `https://predicta-three-zeta.vercel.app/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Access-Control-Allow-Origin: *`
  * Other Info: `The CORS misconfiguration on the web server permits cross-domain read requests from arbitrary third party domains, using unauthenticated APIs on this domain. Web browser implementations do not permit arbitrary third parties to read the response from authenticated APIs, however. This reduces the risk somewhat. This misconfiguration could be used by an attacker to access data that is available in an unauthenticated manner, but which uses some other form of security, such as IP address white-listing.`
* URL: https://predicta-three-zeta.vercel.app/assets/index-DE5c9gQ-.css
  * Node Name: `https://predicta-three-zeta.vercel.app/assets/index-DE5c9gQ-.css`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Access-Control-Allow-Origin: *`
  * Other Info: `The CORS misconfiguration on the web server permits cross-domain read requests from arbitrary third party domains, using unauthenticated APIs on this domain. Web browser implementations do not permit arbitrary third parties to read the response from authenticated APIs, however. This reduces the risk somewhat. This misconfiguration could be used by an attacker to access data that is available in an unauthenticated manner, but which uses some other form of security, such as IP address white-listing.`
* URL: https://predicta-three-zeta.vercel.app/login
  * Node Name: `https://predicta-three-zeta.vercel.app/login`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Access-Control-Allow-Origin: *`
  * Other Info: `The CORS misconfiguration on the web server permits cross-domain read requests from arbitrary third party domains, using unauthenticated APIs on this domain. Web browser implementations do not permit arbitrary third parties to read the response from authenticated APIs, however. This reduces the risk somewhat. This misconfiguration could be used by an attacker to access data that is available in an unauthenticated manner, but which uses some other form of security, such as IP address white-listing.`
* URL: https://predicta-three-zeta.vercel.app/verificar-correo
  * Node Name: `https://predicta-three-zeta.vercel.app/verificar-correo`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Access-Control-Allow-Origin: *`
  * Other Info: `The CORS misconfiguration on the web server permits cross-domain read requests from arbitrary third party domains, using unauthenticated APIs on this domain. Web browser implementations do not permit arbitrary third parties to read the response from authenticated APIs, however. This reduces the risk somewhat. This misconfiguration could be used by an attacker to access data that is available in an unauthenticated manner, but which uses some other form of security, such as IP address white-listing.`

Instances: Systemic


### Solution

Ensure that sensitive data is not available in an unauthenticated manner (using IP address white-listing, for instance).
Configure the "Access-Control-Allow-Origin" HTTP header to a more restrictive set of domains, or remove all CORS headers entirely, to allow the web browser to enforce the Same Origin Policy (SOP) in a more restrictive manner.

### Reference


* [ https://vulncat.fortify.com/en/detail?category=HTML5&subcategory=Overly%20Permissive%20CORS%20Policy ](https://vulncat.fortify.com/en/detail?category=HTML5&subcategory=Overly%20Permissive%20CORS%20Policy)


#### CWE Id: [ 264 ](https://cwe.mitre.org/data/definitions/264.html)


#### WASC Id: 14

#### Source ID: 3

### [ CSP: Header & Meta ](https://www.zaproxy.org/docs/alerts/10055/)



##### Informational (High)

### Description

The message contained both CSP specified via header and via Meta tag. It was not possible to union these policies in order to perform an analysis. Therefore, they have been evaluated individually.

* URL: https://predicta-three-zeta.vercel.app
  * Node Name: `https://predicta-three-zeta.vercel.app`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app/
  * Node Name: `https://predicta-three-zeta.vercel.app/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app/login
  * Node Name: `https://predicta-three-zeta.vercel.app/login`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app/robots.txt
  * Node Name: `https://predicta-three-zeta.vercel.app/robots.txt`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app/verificar-correo
  * Node Name: `https://predicta-three-zeta.vercel.app/verificar-correo`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: ``
  * Other Info: ``

Instances: Systemic


### Solution

Ensure that your web server, application server, load balancer, etc. is properly configured to set the Content-Security-Policy header.

### Reference


* [ https://www.w3.org/TR/CSP/ ](https://www.w3.org/TR/CSP/)
* [ https://caniuse.com/#search=content+security+policy ](https://caniuse.com/#search=content+security+policy)
* [ https://content-security-policy.com/ ](https://content-security-policy.com/)
* [ https://github.com/HtmlUnit/htmlunit-csp ](https://github.com/HtmlUnit/htmlunit-csp)
* [ https://web.dev/articles/csp#resource-options ](https://web.dev/articles/csp#resource-options)


#### CWE Id: [ 693 ](https://cwe.mitre.org/data/definitions/693.html)


#### WASC Id: 15

#### Source ID: 3

### [ Information Disclosure - Suspicious Comments ](https://www.zaproxy.org/docs/alerts/10027/)



##### Informational (Low)

### Description

The response appears to contain suspicious comments which may help an attacker.

* URL: https://predicta-three-zeta.vercel.app/assets/index-iYhewYQk.js
  * Node Name: `https://predicta-three-zeta.vercel.app/assets/index-iYhewYQk.js`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Db`
  * Other Info: `The following pattern was used: \bDB\b and was detected in likely comment: "//www.w3.org/2000/svg",h);break;case 2:m=v.createElementNS("http://www.w3.org/1998/Math/MathML",h);break;default:switch(h){case"", see evidence field for the suspicious comment/snippet.`


Instances: 1

### Solution

Remove all comments that return information that may help an attacker and fix any underlying problems they refer to.

### Reference



#### CWE Id: [ 615 ](https://cwe.mitre.org/data/definitions/615.html)


#### WASC Id: 13

#### Source ID: 3

### [ Modern Web Application ](https://www.zaproxy.org/docs/alerts/10109/)



##### Informational (Medium)

### Description

The application appears to be a modern web application. If you need to explore it automatically then the Ajax Spider may well be more effective than the standard one.

* URL: https://predicta-three-zeta.vercel.app
  * Node Name: `https://predicta-three-zeta.vercel.app`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-iYhewYQk.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://predicta-three-zeta.vercel.app/
  * Node Name: `https://predicta-three-zeta.vercel.app/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-iYhewYQk.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://predicta-three-zeta.vercel.app/login
  * Node Name: `https://predicta-three-zeta.vercel.app/login`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-iYhewYQk.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://predicta-three-zeta.vercel.app/sitemap.xml
  * Node Name: `https://predicta-three-zeta.vercel.app/sitemap.xml`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-iYhewYQk.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`
* URL: https://predicta-three-zeta.vercel.app/verificar-correo
  * Node Name: `https://predicta-three-zeta.vercel.app/verificar-correo`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `<script type="module" crossorigin src="/assets/index-iYhewYQk.js"></script>`
  * Other Info: `No links have been found while there are scripts, which is an indication that this is a modern web application.`

Instances: Systemic


### Solution

This is an informational alert and so no changes are required.

### Reference




#### Source ID: 3

### [ Re-examine Cache-control Directives ](https://www.zaproxy.org/docs/alerts/10015/)



##### Informational (Low)

### Description

The cache-control header has not been set properly or is missing, allowing the browser and proxies to cache content. For static assets like css, js, or image files this might be intended, however, the resources should be reviewed to ensure that no sensitive content will be cached.

* URL: https://predicta-api.up.railway.app
  * Node Name: `https://predicta-api.up.railway.app`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://predicta-api.up.railway.app/
  * Node Name: `https://predicta-api.up.railway.app/`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://predicta-api.up.railway.app/health
  * Node Name: `https://predicta-api.up.railway.app/health`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://predicta-api.up.railway.app/health/db
  * Node Name: `https://predicta-api.up.railway.app/health/db`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: ``
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app
  * Node Name: `https://predicta-three-zeta.vercel.app`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `public, max-age=0, must-revalidate`
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app/
  * Node Name: `https://predicta-three-zeta.vercel.app/`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `public, max-age=0, must-revalidate`
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app/login
  * Node Name: `https://predicta-three-zeta.vercel.app/login`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `public, max-age=0, must-revalidate`
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app/sitemap.xml
  * Node Name: `https://predicta-three-zeta.vercel.app/sitemap.xml`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `public, max-age=0, must-revalidate`
  * Other Info: ``
* URL: https://predicta-three-zeta.vercel.app/verificar-correo
  * Node Name: `https://predicta-three-zeta.vercel.app/verificar-correo`
  * Method: `GET`
  * Parameter: `cache-control`
  * Attack: ``
  * Evidence: `public, max-age=0, must-revalidate`
  * Other Info: ``

Instances: Systemic


### Solution

For secure content, ensure the cache-control HTTP header is set with "no-cache, no-store, must-revalidate". If an asset should be cached consider setting the directives "public, max-age, immutable".

### Reference


* [ https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#web-content-caching ](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html#web-content-caching)
* [ https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control ](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
* [ https://grayduck.mn/2021/09/13/cache-control-recommendations/ ](https://grayduck.mn/2021/09/13/cache-control-recommendations/)


#### CWE Id: [ 525 ](https://cwe.mitre.org/data/definitions/525.html)


#### WASC Id: 13

#### Source ID: 3

### [ Retrieved from Cache ](https://www.zaproxy.org/docs/alerts/10050/)



##### Informational (Medium)

### Description

The content was retrieved from a shared cache. If the response data is sensitive, personal or user-specific, this may result in sensitive information being leaked. In some cases, this may even result in a user gaining complete control of the session of another user, depending on the configuration of the caching components in use in their environment. This is primarily an issue where caching servers such as "proxy" caches are configured on the local network. This configuration is typically found in corporate or educational environments, for instance.

* URL: https://predicta-three-zeta.vercel.app/
  * Node Name: `https://predicta-three-zeta.vercel.app/`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Age: 0`
  * Other Info: `The presence of the 'Age' header indicates that a HTTP/1.1 compliant caching server is in use.`
* URL: https://predicta-three-zeta.vercel.app/assets/index-DE5c9gQ-.css
  * Node Name: `https://predicta-three-zeta.vercel.app/assets/index-DE5c9gQ-.css`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Age: 0`
  * Other Info: `The presence of the 'Age' header indicates that a HTTP/1.1 compliant caching server is in use.`
* URL: https://predicta-three-zeta.vercel.app/login
  * Node Name: `https://predicta-three-zeta.vercel.app/login`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Age: 152`
  * Other Info: `The presence of the 'Age' header indicates that a HTTP/1.1 compliant caching server is in use.`
* URL: https://predicta-three-zeta.vercel.app/login
  * Node Name: `https://predicta-three-zeta.vercel.app/login`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Age: 154`
  * Other Info: `The presence of the 'Age' header indicates that a HTTP/1.1 compliant caching server is in use.`
* URL: https://predicta-three-zeta.vercel.app/verificar-correo
  * Node Name: `https://predicta-three-zeta.vercel.app/verificar-correo`
  * Method: `GET`
  * Parameter: ``
  * Attack: ``
  * Evidence: `Age: 152`
  * Other Info: `The presence of the 'Age' header indicates that a HTTP/1.1 compliant caching server is in use.`

Instances: Systemic


### Solution

Validate that the response does not contain sensitive, personal or user-specific information. If it does, consider the use of the following HTTP response headers, to limit, or prevent the content being stored and retrieved from the cache by another user:
Cache-Control: no-cache, no-store, must-revalidate, private
Pragma: no-cache
Expires: 0
This configuration directs both HTTP 1.0 and HTTP 1.1 compliant caching servers to not store the response, and to not retrieve the response (without validation) from the cache, in response to a similar request.

### Reference


* [ https://datatracker.ietf.org/doc/html/rfc7234 ](https://datatracker.ietf.org/doc/html/rfc7234)
* [ https://datatracker.ietf.org/doc/html/rfc7231 ](https://datatracker.ietf.org/doc/html/rfc7231)
* [ https://www.rfc-editor.org/rfc/rfc9110.html ](https://www.rfc-editor.org/rfc/rfc9110.html)


#### CWE Id: [ 525 ](https://cwe.mitre.org/data/definitions/525.html)


#### Source ID: 3


