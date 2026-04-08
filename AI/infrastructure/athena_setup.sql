-- ============================================================
-- Athena DDL — Tablas externas sobre datos exportados a S3
-- Incomia (Equipo HAIKU)
-- ============================================================
-- Los datos se exportan desde data_generator a S3 en formato
-- JSON-Lines (NDJSON), particionados por year/month/day.
--
-- Estructura en S3:
--   s3://incomia-data-lake/raw/users/year=2026/month=04/day=08/data.jsonl
--   s3://incomia-data-lake/raw/transactions/year=2026/month=04/day=08/data.jsonl
--   s3://incomia-data-lake/raw/expenses/year=2026/month=04/day=08/data.jsonl
--
-- Prerequisito:
--   CREATE DATABASE IF NOT EXISTS incomia_analytics;
-- ============================================================

CREATE DATABASE IF NOT EXISTS incomia_analytics
COMMENT 'Base analitica Incomia - Economia Gig Mexico 2026';

-- ── TABLA: Usuarios ─────────────────────────────────────────

CREATE EXTERNAL TABLE IF NOT EXISTS incomia_analytics.users (
    user_id                    STRING,
    primary_sector             STRING,
    sub_sector                 STRING,
    display_name               STRING,
    email_hash                 STRING,
    phone_hash                 STRING,
    artificial_salary          DOUBLE,
    stabilization_fund_balance DOUBLE,
    resilience_goal_type       STRING,
    resilience_goal_target     DOUBLE,
    current_risk_score         INT,
    created_at                 STRING,
    profile_version            STRING,
    currency                   STRING,
    city                       STRING
)
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES ('ignore.malformed.json' = 'true')
LOCATION 's3://incomia-data-lake/raw/users/'
TBLPROPERTIES ('has_encrypted_data'='false');

-- ── TABLA: Transacciones ────────────────────────────────────

CREATE EXTERNAL TABLE IF NOT EXISTS incomia_analytics.transactions (
    transaction_id STRING,
    user_id        STRING,
    timestamp      STRING,
    amount         DOUBLE,
    currency       STRING,
    type           STRING,
    income_source  STRING,
    payment_method STRING,
    description    STRING
)
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES ('ignore.malformed.json' = 'true')
LOCATION 's3://incomia-data-lake/raw/transactions/'
TBLPROPERTIES ('has_encrypted_data'='false');

-- ── TABLA: Gastos Fijos ─────────────────────────────────────

CREATE EXTERNAL TABLE IF NOT EXISTS incomia_analytics.expenses (
    expense_id       STRING,
    user_id          STRING,
    name             STRING,
    amount           DOUBLE,
    due_day_of_month INT,
    category         STRING,
    is_active        BOOLEAN,
    currency         STRING,
    created_at       STRING
)
PARTITIONED BY (year INT, month INT, day INT)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
WITH SERDEPROPERTIES ('ignore.malformed.json' = 'true')
LOCATION 's3://incomia-data-lake/raw/expenses/'
TBLPROPERTIES ('has_encrypted_data'='false');

-- ── Cargar particiones ──────────────────────────────────────
-- Ejecutar despues de cada exportacion de datos:
MSCK REPAIR TABLE incomia_analytics.users;
MSCK REPAIR TABLE incomia_analytics.transactions;
MSCK REPAIR TABLE incomia_analytics.expenses;

-- ============================================================
-- QUERIES DE EJEMPLO
-- ============================================================

-- Ingreso promedio por sector
-- SELECT primary_sector, AVG(artificial_salary) as avg_salary
-- FROM incomia_analytics.users
-- GROUP BY primary_sector;

-- Transacciones del ultimo mes por usuario
-- SELECT user_id, type, SUM(amount) as total
-- FROM incomia_analytics.transactions
-- WHERE year = 2026 AND month = 4
-- GROUP BY user_id, type;

-- Gastos fijos totales por categoria
-- SELECT category, SUM(amount) as total_mensual
-- FROM incomia_analytics.expenses
-- WHERE is_active = true
-- GROUP BY category
-- ORDER BY total_mensual DESC;
