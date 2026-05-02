CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('Doctor', 'Patient')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS health_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    patient_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    symptoms TEXT NOT NULL,
    body_temperature REAL NOT NULL,
    heart_rate INTEGER NOT NULL,
    preference TEXT NOT NULL CHECK (preference IN ('Allopathy', 'Ayurvedic')),
    created_at TEXT NOT NULL,
    temp_category TEXT NOT NULL,
    heart_category TEXT NOT NULL,
    status TEXT NOT NULL,
    condition TEXT NOT NULL,
    explanation TEXT NOT NULL,
    suggestions TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
