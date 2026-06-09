# Stage 3.5 Pricing + Plans

Stage 3.5 connects the marketing pricing layer with the backend billing plan catalog.

## Backend source of truth

Public endpoints:

- `GET /api/v1/plans`
- `GET /api/v1/plans/{plan_code}`

Current active backend plans:

| Code | Price monthly | Currency | Storage | Transcription seconds | Jobs |
|---|---:|---|---:|---:|---:|
| `free` | 0 | USD | 10 GB | 36,000 | 500 |
| `pro` | 12 | USD | 100 GB | 144,000 | 5,000 |
| `business` | 49 | USD | 500 GB | 720,000 | 20,000 |

## Marketing alignment

The marketing pricing cards must use the same plan codes as backend:

- `free`
- `pro`
- `business`

The public marketing CTA includes a plan code query parameter:

```text
/auth/register?plan=pro
Web alignment

The web pricing and billing pages should show the same monthly pricing as backend.

No migration in this stage

The existing plans table already contains the fields required for this stage:

code
name
price_monthly
currency
storage_bytes_limit
transcription_seconds_limit
jobs_count_limit
is_active