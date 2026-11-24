# Changelog

All notable changes to DeepAI Code Daily are documented in this file.

## [1.0.0] - 2026-11-24

### Added

- Standalone DeepAI Code daily Theos grant runner.
- Multi-account API-key parsing and isolated requests sessions.
- Real-device fingerprint header generation with an explicit override.
- One-request daily trigger using `/deepai_code/theos`.
- Persisted hashed-account refresh_at baseline without storing API keys.
- Honest `GRANT_ACTIVE`, `CLAIMED`, and `ALREADY_GRANTED` outcomes.
- Tests for first grant, repeated grant, refresh_at change, pending grant,
  disabled allowance, restart limit, login expiry, redaction, and isolation.
