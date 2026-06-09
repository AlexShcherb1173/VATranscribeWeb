# Legal Document Versions

The application tracks legal document versions accepted by users.

## Required registration documents

| Backend document type | Marketing route | Version |
|---|---|---|
| `terms` | `/legal/terms` | `1.0` |
| `privacy` | `/legal/privacy` | `1.0` |
| `personal_data` | `/legal/personal-data` | `1.0` |

## Additional public policy pages

| Document type | Marketing route | Version |
|---|---|---|
| `cookies` | `/legal/cookies` | `1.0` |
| `refund` | `/legal/refund` | `1.0` |

## Registration flow

The frontend registration flow sends:

```json
{
  "accepted_legal_documents": [
    {
      "document_type": "terms",
      "document_version": "1.0",
      "accepted": true
    },
    {
      "document_type": "privacy",
      "document_version": "1.0",
      "accepted": true
    },
    {
      "document_type": "personal_data",
      "document_version": "1.0",
      "accepted": true
    }
  ]
}
The backend validates that all required current legal documents are accepted before creating the user.