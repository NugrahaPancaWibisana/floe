# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Dockerfile + docker-compose for containerized deployment (#46)
- GitHub Actions CI workflow (#47)
- Healthcheck endpoint (`/ping`) for Railway uptime monitoring (#49)
- First-run setup wizard for language and currency selection (#50)
- `/settings` command for user preference management (#51)
- Bilingual Gemini system prompt supporting English and Indonesian (#52)
- Multi-currency support with auto-conversion (#64)
- Typing indicator and progress feedback during long operations (#54)
- Improved error messages with actionable guidance (#55)
- Delete confirmation with inline keyboard (#56)
- Idempotency mechanism to prevent duplicate transactions (#57)
- Smart retry when Gemini parsing fails (#58)
- 80% budget threshold warning (#59)
- Recurring transactions for auto-recording monthly bills (#60)
- Transaction search command (`/search`) (#61)
- Spending insights and period comparisons (#62)
- Bank CSV import via Gemini parsing (#63)
- Budget rollover to next month (#65)
- `SECURITY.md` for vulnerability reporting (#67)
- Dependabot configuration for automated dependency updates (#69)
- International amount formats and currency symbols (#53)

### Changed

- Archived `guide.md` — superseded by `README.md`, `CONTRIBUTING.md`, and module-level docstrings (#48)
- Replaced placeholder URLs in `README.md` and `CONTRIBUTING.md` with real links (#66)

## [0.2.0] - 2026-05-13

### Added

- Startup warning when `ALLOWED_USER_IDS` is empty (#26)
- Unit tests for finance helpers (`test/25-unit-coverage`) (#34)

### Fixed

- Trailing slash in webhook URL causing double-slash in requests (#35)
- Empty cells in budget Limit column causing `TypeError` (#43)
- Date format validation on `Transaction.date` field to reject invalid dates (#41)

### Changed

- `GOOGLE_SERVICE_ACCOUNT_B64` env var as primary credential source, with file fallback (#36)
- Extracted `_process_transaction` helper to deduplicate text and photo handler logic (#37)
- `TransactionType` enum used directly in `GeminiOutput` pydantic model for early validation (#38)
- Cached gspread client with `lru_cache` to reduce latency on repeated calls (#39)
- Extracted `_get_transactions_df` to deduplicate date-filtering logic across summary, export, and budget (#40)
- Replaced f-string logging with percent-format (`%s`) for lazy evaluation (#44)
- Added missing type hints to `_format_summary` and scheduler functions (#45)

## [0.1.0] - 2026-05-12

### Added

- Project initialization with `uv`, Python 3.12, core dependencies
- `.env` configuration loader with validation (`config.py`)
- `Transaction` dataclass with domain enums (`TransactionType`, `TransactionCategory`)
- Google Sheets read/write client via `gspread`
- Gemini AI parser for extracting transactions from text and photo messages
- Telegram bot commands: `/start`, `/help`, `/summary`, `/weekly`
- Text and photo message handlers with Gemini-backed parsing
- Daily (21:00 WIB) and weekly (Sunday 20:00 WIB) summary scheduler
- Application entrypoint with `ApplicationBuilder` + `JobQueue` + webhook/polling support
- Unit tests for Gemini transaction parser
- Retry with exponential backoff on Gemini API calls
- `/delete` command to remove the last recorded transaction
- Multi-user support with per-user Google Sheets tabs
- `ALLOWED_USER_IDS` whitelist for access control
- Pydantic models replacing raw dataclasses
- `google-genai` SDK with `response_schema` for structured Gemini output
- `/export` command for monthly CSV export
- `/budget` command with per-category budget tracking and alerts
- Webhook mode with polling fallback for Railway deployment
- Industry-grade `README.md` with architecture, setup, and deployment docs
- Open-source infrastructure: `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
- GitHub issue templates, PR template, and `CODEOWNERS`
- `pyproject.toml` metadata and repository topics
- Decimal number format handling in `/budget` command

[Unreleased]: https://github.com/NugrahaPancaWibisana/floe/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/NugrahaPancaWibisana/floe/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/NugrahaPancaWibisana/floe/releases/tag/v0.1.0
