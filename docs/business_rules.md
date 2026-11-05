# Business rules

## Pickup request
`pending -> approved | rejected | cancelled` · `approved -> assigned | cancelled` · `assigned -> scheduled | approved | cancelled` · `scheduled -> collected | approved | cancelled`.
* Humans may only set `approved` / `rejected` (reason required). `assigned`, `scheduled`, `collected` are driven by the assignment and collection workflows.
* Customer service must be `active`, the address must belong to the customer, the category must be active, quantity > 0, date not in the past.
* A customer sees only their own requests. Cancelling releases any assignment (driver, vehicle, workers become available again).
* A missed/incomplete collection puts the request back to `approved` so it can be re-assigned.

## Assignment (validated on assign and reassign)
* Pickup must be `approved` and have no active assignment.
* Driver / vehicle / workers must be `available` (or already `assigned`), never `on_leave`, `under_maintenance`, `broken_down`, etc.
* **Vehicle capacity >= estimated quantity.**
* Driver licence must still be valid on the collection date.
* No double booking: a driver, vehicle or worker cannot have another active collection within 2 hours.
* Only not-yet-started assignments can be reassigned; every change writes `assignment_history` and an audit row.

## Collection
Start (`assigned -> in_progress`, vehicle `in_service`) -> complete (quantity <= vehicle capacity) **or** incomplete (partial quantity) / missed (no quantity). Photo evidence is stored as validated http(s) URLs. Missed/incomplete notifies management and the customer.

## Transfer -> segregation -> processing -> disposal
* Transfer: center `active`, accepts the category, has free capacity; vehicle usable and large enough; **quantity <= collected stock in that zone/category not already transferred**. `pending -> in_transit -> delivered`; centre load increases on delivery and a capacity alert fires at >= 85 %.
* Segregation: transfer must be delivered; recyclable + non-recyclable + contaminated <= incoming; cannot exceed the transfer quantity cumulatively.
* Processing: input <= waste currently held by the centre (reserved on creation); output + loss <= input; yield % calculated on completion; a failed batch returns stock.
* Disposal: needs approval by operations manager / super admin; **the responsible person cannot approve their own disposal**; approval deducts centre stock.
* A recycling-center manager can only operate on the centre they manage.

## Vehicles & maintenance
* `assigned` / `in_service` are set automatically; humans may set `available`, `under_maintenance`, `broken_down`, `retired`.
* A vehicle with open maintenance cannot be marked available. Planned service cannot start while the vehicle has active assignments.
* Breakdown report -> vehicle `broken_down`, urgent request, management + supervisors notified (with count of affected upcoming collections).
* Completing maintenance records cost, **downtime hours** (from the breakdown report, or from start of planned work), a history row, updates the vehicle's service dates and rolls preventive schedules forward.

## Complaints
`open -> assigned -> in_progress -> resolved -> closed` (resolved can be re-opened to in_progress; `rejected` is terminal). Remarks are mandatory to resolve/reject. Every change is stored in `complaint_history` and the customer is notified.

## Users
Cannot deactivate yourself or change your own role; only a super admin can touch another super admin. Deactivation revokes all refresh tokens.
