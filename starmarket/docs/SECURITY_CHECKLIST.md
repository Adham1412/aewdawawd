# Security checklist before production

- [ ] `SESSION_SECRET` is random, secret, and at least 32 characters.
- [ ] Telegram bot token stored only in secret storage / environment.
- [x] Telegram Mini App `initData` validated server-side (tests exist; run them).
- [ ] Session revocation store implemented if instant revocation is required.
- [x] Admin access = Telegram ID allow-list checked on every request (no passwords). Per-action RBAC is NOT implemented yet (single admin role).
- [ ] CORS contains only deployed trusted origins.
- [ ] Rate limiting uses shared/persistent storage across replicas.
- [ ] Database credentials have least privilege; TLS enabled where supported.
- [ ] Alembic migrations reviewed and tested.
- [ ] Payment webhooks verify signatures and are idempotent.
- [x] Ledger writes are transactional, append-only and idempotent via unique reference.
- [ ] No secrets or personal data in logs.
- [ ] Backup encryption, separate storage and restore drills verified.
- [ ] Product fulfilment method approved and tested.
- [x] No customer password or login-code collection (schema rejects such fields).
- [ ] Dependency audit, tests, security review and rollback plan completed.
