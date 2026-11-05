# Architecture

Layered FastAPI application. Each request flows one way:

```
HTTP -> endpoint (api/v1/endpoints) -> service -> repository -> SQLAlchemy model -> database
              |  validates input (schemas)        |  owns the transaction + audit log + notifications
              |  enforces role (dependencies)     |  business rules live HERE
```

| Layer | Folder | Responsibility |
|---|---|---|
| Endpoints | `app/api/v1/endpoints` | HTTP only: parse, authorise (`require_roles`), call one service method, return a schema |
| Schemas | `app/schemas` | Pydantic request/response models and field validation |
| Services | `app/services` | Business rules, state machines, capacity checks, transactions, audit and notification side effects |
| Repositories | `app/repositories` | Queries and filters; soft-delete aware; never commit |
| Models | `app/models` | SQLAlchemy tables (all inherit id, timestamps, soft delete) |
| Core | `app/core` | Config, password hashing, JWT, Google OAuth client, errors, pagination |

## Transactions
Repositories only `flush()`. A service wraps every multi-step write in `with transaction(db):`, which commits on success and rolls back on any exception. The entity change, its audit log row and any notifications are therefore saved together or not at all.

## Authentication
* **OAuth2 password flow** - `POST /auth/login` accepts a form (`username` = e-mail). Swagger's *Authorize* button uses it.
* **JWT access token** (30 min) + **refresh token** (7 days). Refresh tokens are tracked by `jti` in `refresh_tokens`, are single-use (rotation), and are revoked on logout, password change/reset and deactivation.
* **Google OAuth2 sign-up/login** - `GET /auth/google/login` -> Google consent -> `GET /auth/google/callback`. First login creates a `customer` user plus customer profile; later logins reuse it; an existing local account with the same *verified* e-mail is linked. See `docs/api_documentation.md`.
* Public registration can only ever create `customer` accounts. Staff accounts are created by a super admin (`POST /users`).

## Error format
Every error has the same shape (validation, auth, business rule, 404, 500):
```json
{"success": false, "error": {"code": "business_rule_violation", "message": "...", "details": null}, "request_id": "..."}
```

## Security notes
* Passwords: bcrypt. Strength policy enforced by schema validation.
* Reset tokens are stored hashed, expire in 30 min and are single use. `/forgot-password` never reveals whether an e-mail exists.
* Soft delete everywhere (`is_deleted`); deleted users can no longer authenticate.
* CSV export neutralises spreadsheet-formula injection.
* The app refuses to start in `production` with the default `SECRET_KEY`.
