-- ============================================================
-- Predicta - Database Schema
-- ============================================================
-- This file is kept as a reference of the initial schema.
-- For ongoing schema changes, use Alembic migrations:
--     cd backend && alembic revision --autogenerate -m "description"
--     cd backend && alembic upgrade head
--
-- Apply this seed manually only if NOT using Alembic (e.g., quick
-- local setup). When using Alembic, run `alembic upgrade head`.
-- ============================================================

-- 1. Roles
CREATE TABLE IF NOT EXISTS roles (
    id_rol      SERIAL PRIMARY KEY,
    nombre_rol  VARCHAR(50) UNIQUE NOT NULL
);

-- 2. Users
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario          SERIAL PRIMARY KEY,
    nombre_usuario      VARCHAR(50) UNIQUE NOT NULL,
    correo_electronico  VARCHAR(100) UNIQUE NOT NULL,
    contrasena_hash     TEXT NOT NULL,
    id_rol              INTEGER REFERENCES roles(id_rol) ON DELETE SET NULL,
    fecha_registro      TIMESTAMP DEFAULT NOW()
);

-- 3. Sales (single unified table)
CREATE TABLE IF NOT EXISTS ventas (
    id_venta        SERIAL PRIMARY KEY,
    id_usuario      INTEGER NOT NULL REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    producto        VARCHAR(150) NOT NULL,
    monto           DECIMAL(10, 2) NOT NULL,
    categoria       VARCHAR(100),
    fecha_venta     DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_ventas_usuario      ON ventas (id_usuario);
CREATE INDEX IF NOT EXISTS idx_ventas_fecha        ON ventas (fecha_venta);
CREATE INDEX IF NOT EXISTS idx_ventas_categoria    ON ventas (categoria);
CREATE INDEX IF NOT EXISTS idx_ventas_usuario_fecha ON ventas (id_usuario, fecha_venta);

-- 4. Files (ETL ingestion tracking)
CREATE TABLE IF NOT EXISTS archivos (
    id_archivo          SERIAL PRIMARY KEY,
    id_usuario          INTEGER REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    nombre_original     VARCHAR(255) NOT NULL,
    ruta_servidor       TEXT NOT NULL,
    estado_proceso      VARCHAR(20) DEFAULT 'Pendiente',
    filas_procesadas    INTEGER DEFAULT 0,
    fecha_subida        TIMESTAMP DEFAULT NOW()
);

-- 5. Predictions (model output history)
CREATE TABLE IF NOT EXISTS predicciones (
    id_prediccion           SERIAL PRIMARY KEY,
    id_usuario              INTEGER REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    producto_referencia     VARCHAR(150) NOT NULL,
    cantidad_proyectada     DECIMAL(10, 2) NOT NULL,
    fecha_proyeccion        DATE NOT NULL,
    precision_estimada      DECIMAL(5, 2),
    fecha_creacion          TIMESTAMP DEFAULT NOW()
);

-- Base roles
INSERT INTO roles (nombre_rol) VALUES
    ('Administrador'),
    ('Usuario')
ON CONFLICT (nombre_rol) DO NOTHING;
