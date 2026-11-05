# Database schema (33 tables incl. `alembic_version`)

All business tables carry `id`, `created_at`, `updated_at`, `is_deleted`, `deleted_at`. Append-only tables (history, audit, notifications, tokens) omit the soft-delete columns.

| Area | Tables |
|---|---|
| Auth | `users`, `refresh_tokens`, `password_resets` |
| Locations | `service_zones`, `collection_areas`, `streets`, `collection_schedules` |
| Waste | `waste_categories`, `segregation_rules` |
| Customers | `customers`, `customer_addresses` (latitude/longitude for mapping) |
| Pickups | `pickup_requests` |
| Fleet & people | `vehicles`, `vehicle_maintenance` (history), `drivers`, `field_workers` |
| Assignment | `collection_assignments`, `assignment_workers` (m2m), `assignment_history`, `collection_records` |
| Recycling | `recycling_centers`, `center_waste_categories`, `waste_transfers`, `waste_segregations`, `processing_batches`, `disposal_records` |
| Maintenance | `maintenance_requests`, `maintenance_schedules` |
| Complaints | `complaints`, `complaint_history` |
| System | `notifications`, `audit_logs` |

## Key relationships
```
service_zones 1-* collection_areas 1-* streets
service_zones 1-* customers 1-* customer_addresses
customers 1-* pickup_requests *-1 waste_categories
pickup_requests 1-* collection_assignments (one active at a time) *-1 drivers, vehicles; *-* field_workers
collection_assignments 1-* collection_records (start / complete / incomplete)
recycling_centers *-* waste_categories (accepted)
waste_transfers: zone -> center (vehicle, category, kg)  ->  waste_segregations -> processing_batches / disposal_records
```

## Indexes
Unique: e-mail, registration number, licence number, employee code, every business number (`PR-…`, `TR-…`, `PB-…`, `DS-…`, `CMP-…`), zone/area/category/center codes, `(zone_id, area name)`, `(center_id, category_id)`.
Indexed for filtering: every `status`, `is_deleted`, `role`, `is_active`, all foreign keys used in joins, `preferred_date`, `scheduled_at`, `processing_date`, `disposal_date`, audit `action`/`entity`.

## Migrations
`alembic/versions/0001_initial_schema.py` creates everything. Verified: upgrade -> downgrade -> upgrade, and autogenerate reports no drift from the models.
