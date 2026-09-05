# HARSH TRADER AI — Database Schema & Data Dictionary (PostgreSQL)

## Core Entities & Relational Design

### 1. `users`
Stores system accounts & authentication credentials.
- `id` (UUID, Primary Key)
- `email` (VARCHAR 255, Unique, Indexed)
- `hashed_password` (VARCHAR 255)
- `role` (VARCHAR 50) — `ADMIN`, `TRADER`

### 2. `user_risk_profiles`
Configurable capital allocation and position risk caps per user.
- `user_id` (FK -> users.id)
- `total_capital` (NUMERIC 15,2) — Default `₹100,000.00`
- `risk_per_trade_pct` (NUMERIC 5,2) — Default `1.0%`
- `max_position_size_pct` (NUMERIC 5,2) — Default `15.0%`
- `max_daily_loss_pct` (NUMERIC 5,2) — Default `3.0%`

### 3. `stocks`
Universe master table for NSE/BSE securities.
- `symbol` (VARCHAR 50, Unique, Indexed)
- `company_name` (VARCHAR 255)
- `exchange` (VARCHAR 10) — `NSE` / `BSE`
- `upper_circuit_limit` (NUMERIC 10,2)
- `lower_circuit_limit` (NUMERIC 10,2)

### 4. `market_data_snapshots`
Immutable historical OHLCV candles and quality metadata.
- `symbol` (VARCHAR 50, Indexed)
- `timeframe` (VARCHAR 10) — `5m`, `15m`, `1h`, `1D`
- `data_quality_score` (NUMERIC 5,2)
- `provider` (VARCHAR 50)

### 5. `trade_signals` & `signal_versions`
Signal fingerprinting deduplication and version audit control.
- `signal_fingerprint` (VARCHAR 100, Unique, SHA-256 hash)
- `status` (VARCHAR 30) — `APPROVED`, `REJECTED`, `ACTIVE`, `STOPPED`
- `consensus_score` (NUMERIC 5,2)
- `risk_reward_ratio` (NUMERIC 5,2)
