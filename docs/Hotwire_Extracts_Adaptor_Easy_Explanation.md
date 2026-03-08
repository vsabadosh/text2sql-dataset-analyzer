# Hotwire Extracts Adapter API (Easy Explanation)

This document explains, in simple terms, what the API does and how to use it.

## What this API is for

The **Hotwire Bill Ingestion Adapter** API starts the bill extraction process.

In practice:

1. A bill extract package is uploaded (for example to S3).
2. A pre-processing step (decryption + antivirus) is completed.
3. This API is called to start the extraction workflow.
4. Processing continues asynchronously in backend services.

So this API is the **"start button"** for ingestion.

## Base information

- **Service:** Hotwire Bill Ingestion Adapter
- **Base path:** `/hotwire-adapter/v1`
- **Main endpoint:** `POST /extractAdapter/start`
- **Response pattern:** async start (`202 Accepted` when request is accepted)

## Endpoint you call

`POST /hotwire-adapter/v1/extractAdapter/start`

### Header (optional)

- `Accept-Language` (example: `en-US`)

### Request body (required)

You must send JSON with:

- `url` - where the extract package is stored (S3 or file system)
- `extractName` - extract identifier (must follow expected naming pattern)

Example:

```json
{
  "url": "s3://coreExtracts/00650-01262026_06-01262026-93201_002.tar.gz",
  "extractName": "00650-01262026_06-01262026-93201_002"
}
```

## Naming convention (important)

The extract naming should follow this kind of pattern:

`<corp>-<cycle_date>_<cycle_group>-<run_date>-<freeText>_<batch>`

If naming or input format is wrong, the API can reject with `400 Bad Request`.

## What happens after you call it

After acceptance, the adapter service:

- validates request input,
- splits extract into batches,
- normalizes/maps bills to TMF v4,
- creates run/batch tracking entities,
- dispatches bills for ingestion,
- coordinates with core extractor components.

## Response codes you should expect

- `202 Accepted` - request accepted, extraction started asynchronously.
- `400 Bad Request` - malformed request, missing fields, invalid values.
- `401 Unauthorized` - missing/invalid authentication.
- `403 Forbidden` - caller has no permission.
- `500 Internal Server Error` - unexpected server issue.

## Error payload (simplified)

When an error is returned, the payload can include fields such as:

- `code` (error code),
- `reason` (human-readable reason),
- `message` (additional details),
- `traceId` (important for troubleshooting),
- `@type` (error type).

For support/debug, always capture `traceId`.

## Minimal curl example

```bash
curl -X POST "https://<host>/hotwire-adapter/v1/extractAdapter/start" \
  -H "Content-Type: application/json;charset=utf-8" \
  -H "Accept: application/json;charset=utf-8" \
  -d '{
    "url": "s3://coreExtracts/00650-01262026_06-01262026-93201_002.tar.gz",
    "extractName": "00650-01262026_06-01262026-93201_002"
  }'
```

## Practical checklist before calling API

- Verify package exists at the provided `url`.
- Verify `extractName` matches convention exactly.
- Ensure authentication/authorization is configured.
- Log request ID and capture response body on failures.
- Save `traceId` from error responses for incident analysis.

