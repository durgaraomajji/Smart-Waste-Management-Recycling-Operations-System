# API documentation

Interactive docs: **Swagger UI** `/docs` · **ReDoc** `/redoc` · OpenAPI JSON `/openapi.json`. Base path `/api/v1`. A ready-made **Postman collection** is in `postman/` (151 requests; run *OAuth2 password login* first, it stores the token).

Lists are paginated (`?page=1&page_size=20`, max 100) and return `{items, total, page, page_size, pages}`.

## Authentication

| Endpoint | Purpose |
|---|---|
| `POST /auth/register` | Public sign-up (always a `customer`) |
| `POST /auth/login` | **OAuth2 password flow** - form fields `username` (e-mail) + `password` |
| `POST /auth/login/json` | Same, JSON body `{email, password}` |
| `POST /auth/refresh` | Rotate tokens (`{refresh_token}`), old refresh token is revoked |
| `POST /auth/logout` | Revoke a refresh token |
| `POST /auth/forgot-password`, `/reset-password`, `/change-password` | Password reset (30 min, single-use token) |
| `GET /auth/me` | Current user |
| `GET /auth/google/login` | Start **Google OAuth2** sign-in / sign-up (browser redirect) |
| `GET /auth/google/callback` | Google redirects here; returns tokens and `is_new_user` |
| `GET /auth/google/status` | Is Google sign-in configured? |

Send `Authorization: Bearer <access_token>` on every protected call.

### Setting up Google OAuth2 sign-up
1. Google Cloud Console -> *APIs & Services* -> *Credentials* -> **Create OAuth client ID** (type *Web application*).
2. Add the authorised redirect URI exactly as `GOOGLE_REDIRECT_URI` (default `http://localhost:8000/api/v1/auth/google/callback`).
3. Put `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and a random `SESSION_SECRET` in `.env`, restart.
4. Open `http://localhost:8000/api/v1/auth/google/login` in a browser. After consent the callback returns:
```json
{"access_token": "...", "refresh_token": "...", "token_type": "bearer", "expires_in": 1800, "is_new_user": true}
```
Behaviour: unknown Google account -> a `customer` user + customer profile are created (no password; `auth_provider=google`). Same Google account again -> signs in. Existing local account with the same **verified** e-mail -> accounts are linked. Unverified Google e-mails and deactivated users are refused. Without credentials the endpoints answer `501`.

> For a browser/SPA front end, redirect the user to `/auth/google/login` and have the callback page read the JSON, or change the callback to redirect to your front end with the tokens.

## Roles
`super_admin` (passes every check) · `operations_manager` · `collection_supervisor` · `driver` · `recycling_center_manager` · `field_worker` · `customer`

| Area | Who |
|---|---|
| Users, roles, delete | super admin (list / activate: + operations manager) |
| Zones, areas, categories, vehicles, centres | operations manager (+ super admin); read: any user / staff |
| Customers, pickup approval, assignments, workforce, complaints | collection supervisor and up |
| Collection start/complete | assigned driver / field worker, supervisors |
| Transfers, segregation, processing, disposal | recycling-center manager (own centre only), management |
| Disposal approval | operations manager / super admin (not the requester) |
| Dashboard, reports, analytics, audit logs | operations manager / super admin |
| Own profile, pickups, complaints | customer |

## Endpoint index (by Swagger tag)
* **Authentication** `/auth/*` · **Users** `/users`
* **Locations** `/locations/zones|areas|streets|schedules` (zone status, supervisor assignment, filters)
* **Waste Categories** `/waste-categories` (+ `/segregation-rules`)
* **Customers** `/customers` (+ `/addresses`, `/service-status`, `/collections` history, `/me`)
* **Pickup Requests** `/pickup-requests` (+ `/status`, `/cancel`)
* **Vehicles** `/vehicles` (+ `/status`, `/availability`, `/maintenance-records`)
* **Drivers & Workers** `/workforce/drivers|workers` (+ `/status`, `/supervisor`, `/history`)
* **Collection Assignments** `/assignments` (+ `/reassign`, `/schedule`, `/history`)
* **Collection Tracking** `/collections` (`/start`, `/{id}/complete`, `/{id}/incomplete`)
* **Recycling Centers** `/recycling-centers` (+ `/manager`, `/accepted-categories`, `/availability`)
* **Waste Transfers** `/transfers` (+ `/status`, `/stock`)
* **Waste Segregation** `/segregation` · **Recycling Processing** `/processing/batches` (+ `/start`, `/complete`, `/fail`)
* **Disposal** `/disposals` (+ `/decision`, `/complete`)
* **Vehicle Maintenance** `/maintenance/requests|breakdowns|schedules|due-check`
* **Customer Complaints** `/complaints` (+ `/assign`, `/status`, `/history`)
* **Notifications** `/notifications` (+ `/unread-count`, `/read`, `/read-all`)
* **Analytics** `/analytics/collection-performance|zones|drivers|vehicles|environmental-impact`
* **Admin Dashboard** `/dashboard`
* **Reports** `/reports/{name}` and `/reports/{name}/export` (CSV)
* **Audit Logs** `/audit-logs` (filter by actor, action, entity, dates)

## Reports
Names: `daily-collection`, `monthly-collection`, `zone-performance`, `driver-performance`, `vehicle-utilization`, `waste-category`, `recycling-center-performance`, `recycling-yield`, `disposal`, `environmental-impact`.
Query: `date_from`, `date_to`, `zone_id`, `waste_category_id`, `status`, `sort_by` (any column of the report), `order=asc|desc`, `page`, `page_size`. `/export` returns the full result as `text/csv`.

## Status codes
`200` ok · `201` created · `400` bad input · `401` missing/invalid token · `403` role or ownership · `404` not found · `409` duplicate · `422` validation or business-rule violation · `501` Google not configured · `500` unexpected (logged with a `request_id`).
