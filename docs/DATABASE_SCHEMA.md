# Database Schema

## `users`

- `email`: unique worker login
- `password_hash`: hashed password
- `name`: worker name
- `location`: `{ lat, lon }`
- `work_type`: delivery, driver, courier, or custom type
- `weekly_earnings_estimate`: pricing and payout base
- `last_known_location`: latest claim or profile location snapshot
- `movement_profile`: mock movement baseline used for fraud scoring
- `created_at`, `updated_at`

## `policies`

- `user`: reference to `users`
- `plan_name`: currently `Weekly Income Shield`
- `status`: active, expired, cancelled
- `weekly_premium`: dynamic weekly premium
- `coverage_amount`: payout cap basis
- `risk_score`: composite pricing risk
- `weather_risk`, `historical_risk`, `zone_risk`
- `auto_renew`: boolean
- `current_term_start`, `current_term_end`
- `renewal_count`
- `pricing_breakdown`: component-level pricing details
- `renewal_history`: list of auto-renew events
- `created_at`, `updated_at`

## `claims`

- `user`: reference to `users`
- `policy`: reference to `policies`
- `incident_at`, `submitted_at`
- `location`: `{ lat, lon }`
- `reason`
- `description`
- `proof_files`: uploaded proof metadata
- `ai_validation`: document, image, and weather validation output
- `fraud_score`
- `fraud_signals`: model features and adversarial signals
- `risk_score`
- `risk_breakdown`
- `zone_id`
- `group_fraud`
- `review_required`
- `decision`: APPROVED, REJECTED, FLAGGED, PENDING
- `decision_reason`
- `payout_amount`

## `zone_risks`

- `zone_id`: rounded micro-zone key
- `label`
- `centroid`: representative location
- `weather_risk`
- `historical_risk`
- `location_risk`
- `overall_risk`
- `claim_count`
- `active_alerts`
- `sources`
- `last_updated`

