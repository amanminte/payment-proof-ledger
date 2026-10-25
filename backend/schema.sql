CREATE TABLE IF NOT EXISTS sales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    amount      REAL    NOT NULL CHECK (amount > 0),
    cost        REAL,                                  -- optional, for profit (FR-07)
    status      TEXT    NOT NULL DEFAULT 'pending',    -- pending | verified (yellow/red are computed from age)
    created_at  TEXT    NOT NULL,
    verified_at TEXT,
    payment_id  INTEGER REFERENCES payments(id)
);

CREATE TABLE IF NOT EXISTS payments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    provider        TEXT,
    amount          REAL NOT NULL,
    txn_id          TEXT NOT NULL UNIQUE,
    received_at     TEXT NOT NULL,
    matched_sale_id INTEGER REFERENCES sales(id)
);

CREATE TABLE IF NOT EXISTS alerts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id     INTEGER REFERENCES sales(id),
    type        TEXT NOT NULL,   -- waiting | no_payment | wrong_amount | duplicate_txn
    created_at  TEXT NOT NULL,
    resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS ledger (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id    INTEGER NOT NULL REFERENCES sales(id),
    amount     REAL    NOT NULL,
    created_at TEXT    NOT NULL,
    prev_hash  TEXT    NOT NULL,
    hash       TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK (role IN ('owner', 'cashier')),
    created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS access_tokens (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    token      TEXT NOT NULL UNIQUE,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    is_used    INTEGER NOT NULL DEFAULT 0
);
