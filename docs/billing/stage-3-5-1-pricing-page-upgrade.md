# Stage 3.5.1 Pricing Page Upgrade

Stage 3.5.1 improves the public pricing pages after backend `/api/v1/plans` was exposed.

## Implemented

- Stronger EN/RU pricing page structure
- Backend-aligned plan cards
- Monthly/yearly UI foundation
- Quota matrix
- Feature comparison table
- Billing FAQ
- CTA links with `plan` query parameter
- Additional pricing-specific CSS

## Source of truth

Current backend plans:

| Code | Monthly | Storage | Transcription | Jobs |
|---|---:|---:|---:|---:|
| `free` | `$0` | `10 GB` | `36,000 sec` | `500` |
| `pro` | `$12` | `100 GB` | `144,000 sec` | `5,000` |
| `business` | `$49` | `500 GB` | `720,000 sec` | `20,000` |

## Notes

Yearly billing is only a UI foundation in this stage. A future billing stage should add backend annual pricing fields, migration, provider integration and checkout logic.

No backend migration is required for this stage.