# API Reference

Base URL: `http://localhost:5000/api`

All protected routes require:

```http
Authorization: Bearer <JWT_TOKEN>
```

## Auth

### `POST /auth/register`

Request:

```json
{
  "name": "Asha Rider",
  "email": "asha@example.com",
  "password": "Secret123!",
  "work_type": "delivery",
  "weekly_earnings_estimate": 4500,
  "location": {
    "lat": 12.9716,
    "lon": 77.5946
  }
}
```

Response:

```json
{
  "token": "jwt-token",
  "user": {
    "id": "661...",
    "email": "asha@example.com",
    "name": "Asha Rider"
  }
}
```

### `POST /auth/login`

Request:

```json
{
  "email": "asha@example.com",
  "password": "Secret123!"
}
```

### `GET /auth/me`

Returns the authenticated user profile.

## User

### `GET /users/profile`

Returns the profile for the logged-in worker.

### `PUT /users/profile`

Request:

```json
{
  "name": "Asha Rider",
  "work_type": "delivery",
  "weekly_earnings_estimate": 5200,
  "location": {
    "lat": 12.9716,
    "lon": 77.5946
  }
}
```

## Policy

### `GET /policies/quote`

Returns a dynamic weekly premium quote using weather risk, historical disruption seeds, micro-zone risk, a pricing ML model, a safe-zone discount, and predictive coverage hours.

### `POST /policies/buy`

Creates an active weekly policy if none exists, or returns the current active policy.

Response fields include:

- `weekly_premium`
- `coverage_amount`
- `coverage_hours`
- `risk_score`
- `current_term_start`
- `current_term_end`
- `auto_renew`
- `pricing_breakdown.ml_pricing_delta`
- `pricing_breakdown.safe_zone_discount`
- `pricing_breakdown.zone_snapshot.automated_triggers`

### `GET /policies/current`

Returns the latest synced policy. If no policy exists, returns `404`.

### `POST /policies/cancel`

Cancels the current policy and disables auto-renewal.

## Claims

### `POST /claims/submit`

Accepts `multipart/form-data`.

Form fields:

- `incident_at`
- `reason`
- `description`
- `lat`
- `lon`
- `proofs` optional, repeatable file field

Response:

```json
{
  "claim": {
    "decision": "APPROVED",
    "fraud_score": 0.27,
    "payout_amount": 2980.0,
    "ai_validation": {
      "overall_confidence": 0.68
    }
  }
}
```

### `GET /claims/mine`

Returns all claims submitted by the current user.

### `GET /claims/:claimId`

Returns a single claim if it belongs to the current user.

## AI Validation

### `POST /ai/verify-document`

Request:

```json
{
  "reason": "rain",
  "description": "Heavy rain flooded the delivery route and orders were cancelled."
}
```

### `POST /ai/verify-image`

Accepts `multipart/form-data` with `proofs`.

### `POST /ai/verify-weather`

Request:

```json
{
  "reason": "pollution",
  "incident_at": "2026-04-04T10:00:00",
  "location": {
    "lat": 28.6139,
    "lon": 77.2090
  }
}
```

### `POST /ai/active-triggers`

Returns the currently active automated disruption triggers for a supplied location, or for the authenticated worker's saved location if no payload is sent.

Response fields include:

- `automated_triggers`
- `waterlogging_risk`
- `forecast_disruption_hours`
- `civic_alert`

## Dashboard

### `GET /dashboard/summary`

Returns:

- total platform claims
- approved, rejected, and flagged counts
- fraud alerts
- high-risk zones
- current user recent claims
- current user active policy
- current user active disruption triggers
