# StarMarket architecture notes

## Principles
- API is versioned under `/api/v1`.
- Business rules live in backend services, not in browser code.
- Product prices are read from the database; the client cannot submit a trusted price.
- Order creation requires an idempotency key.
- Payment is not implemented in this starter; no real charge or fulfilment occurs.
- Telegram Mini App identity is accepted only after server-side `initData` verification.
- Sensitive production operations require server-side authorization, audit events and confirmation.

## Deployment split
- `app.bot.main`: Telegram long-polling bot service.
- `app.main`: REST API service.
- PostgreSQL: persistent database.
- `web/miniapp`: static Telegram Mini App files.
- `web/admin`: unprotected placeholder only; do not publish until admin auth/RBAC is implemented.

## Order flow planned for production
1. Verify user session.
2. Validate product availability and required destination fields.
3. Recalculate price on server.
4. Create order and idempotency record transactionally.
5. Create payment intent via provider adapter.
6. Verify provider webhook signature and query provider state when uncertain.
7. Record payment and ledger entries transactionally.
8. Enqueue fulfilment through an outbox/worker.
9. Verify delivery evidence; send uncertain cases to admin review.
10. Reconcile provider settlement against internal ledger.
