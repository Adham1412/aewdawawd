# Build status (v0.2)

## Implemented
- Order state machine with ledger (payment/refund, idempotent) and audit records.
- Customer API: auth, catalog, payment info, create/list/get/cancel orders.
- Admin API (Telegram-ID based): orders list + transitions, products create/edit, stats, audit.
- Bot: Mini App buttons, `/orders`, payment receipt intake -> admins notified.
- Mini App (catalog, checkout, payment instructions, my orders) and Admin UI (orders, products, stats, audit), served by the API at `/app/` and `/admin-ui/`.
- Fixes to the starter: wheel packaging (`pip install .` previously could not build), Dockerfile/Compose (migrations, web files, non-root user), PostgreSQL schema created only via Alembic, httpx no longer able to log the bot token, alembic moved to runtime dependencies.

## Checked in the build environment
- Python compile of all modules; Ruff F/E9 (no undefined names/unused imports); JS syntax check (node).
- 11 dependency-free tests passed: order state machine (6), request schema validation incl. rejection of password/code fields (5).

## NOT executed here (PyPI was blocked, so FastAPI/SQLAlchemy/aiogram could not be installed)
- `tests/test_api_flow.py` and `tests/test_security.py` (need installed dependencies) — run `pytest -q` first.
- API server, bot polling, Alembic migration on PostgreSQL, Docker image, Mini App inside Telegram.
Expect to fix small integration issues on the first run; tell us the traceback.

## Not production-ready until
- Real fulfilment path for Stars/Premium confirmed and tested; payment provider integration (if wanted).
- Legal/tax/Telegram-terms review; backups + restore test; HTTPS hosting; monitoring.
