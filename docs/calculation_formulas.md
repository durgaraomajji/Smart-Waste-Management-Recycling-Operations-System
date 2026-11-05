# Calculation formulas and assumptions

All quantities are kilograms. Percentages are rounded to 2 decimals; any division by zero returns 0.

| Metric | Formula | Source rows |
|---|---|---|
| Recycling yield % (batch) | `recycled_output_kg / input_quantity_kg x 100` | processing batch |
| Processing loss % | `processing_loss_kg / input_quantity_kg x 100` | processing batch |
| Collection efficiency % | `completed / (total requests - cancelled - rejected) x 100` | pickup requests |
| Completed pickups | requests with status `collected` | pickup requests |
| Missed pickups | collection records with status `missed` | collection records |
| Average collection time (min) | mean of `completed_at - started_at` for `completed` records | collection records |
| Zone efficiency % | zone `collected / (zone requests - cancelled - rejected) x 100` | pickup requests by zone |
| Driver efficiency % | `completed records / all records x 100` per driver | collection records |
| Vehicle utilisation % | `collected_kg / (capacity_kg x trips) x 100` (average load factor) | records with status completed/incomplete |
| Total waste collected | sum of `collected_quantity_kg` where status is `completed` or `incomplete` | collection records |
| Total recyclable | sum of `recyclable_kg` | segregation records |
| Total recycled | sum of `recycled_output_kg` where batch is `completed` | processing batches |
| Total disposed | sum of `quantity_kg` where disposal is `approved` or `disposed` | disposal records |
| Recycling % | `total recycled / total collected x 100` | as above |
| Category distribution % | `category collected kg / total collected kg x 100` | collection records |
| Monthly recycling trend | per `YYYY-MM`: `recycled / input x 100` for completed batches | processing batches |
| Centre utilisation % | `current_load_kg / daily_capacity_kg x 100` | recycling centre |
| Available transfer stock | `collected (zone, category) - non-cancelled transfers (zone, category)` | records, transfers |

## Assumptions
* Soft-deleted rows are excluded everywhere.
* The **zone filter applies to collection figures only**; segregation, processing and disposal are centre-level and carry no zone.
* Date filters use `preferred_date` for pickups, `created_at` for collection/segregation records, `processing_date` for batches and `disposal_date` for disposals.
* `centre.current_load_kg` is the waste physically on site: it rises on delivered transfers, is reserved (reduced) when a processing batch is created, is returned if the batch fails, and is reduced when a disposal is approved.
* "Recycling %" is a ratio of recycled output to **collected** tonnage over the same filter window; it can be 0 even with processed waste if nothing was collected in that window.
* A 2-hour slot is assumed for clash detection between collections.
