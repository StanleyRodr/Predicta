# Seguridad JWT

Predicta usa `PyJWT` para firmar y validar tokens Bearer con algoritmo HS256.
La migracion reemplaza `python-jose` sin cambiar el contrato publico.

- Claim de identidad: `sub`, como identificador de usuario en texto.
- Claim de expiracion: `exp`, configurado por `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Algoritmo: `HS256`, declarado explicitamente al crear y validar.
- Error de token invalido, expirado o sin `sub`: HTTP 401 generico.

Tokens existentes conservan formato y claims. La migracion no invalida tokens
activos; se rechazan al expirar normalmente. Rotar `SECRET_KEY` requiere una
estrategia operativa separada porque invalida todos los tokens activos.
