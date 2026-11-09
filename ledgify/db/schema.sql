-- Migration 0001: initial schema
CREATE TABLE categories (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('expense', 'income')),
    colour      TEXT NOT NULL DEFAULT '#8c8c8c',
    is_default  INTEGER NOT NULL DEFAULT 0,
    is_archived INTEGER NOT NULL DEFAULT 0,
    UNIQUE (name, type)
);

CREATE TABLE transactions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT NOT NULL,
    amount         INTEGER NOT NULL CHECK (amount > 0),
    type           TEXT NOT NULL CHECK (type IN ('expense', 'income')),
    category_id    INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    note           TEXT NOT NULL DEFAULT '',
    payment_method TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL,
    updated_at     TEXT NOT NULL
);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_category ON transactions(category_id);

CREATE TABLE budgets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    month       TEXT NOT NULL,
    limit_cents INTEGER NOT NULL CHECK (limit_cents > 0),
    UNIQUE (category_id, month)
);

CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE schema_version (
    version INTEGER NOT NULL
);
