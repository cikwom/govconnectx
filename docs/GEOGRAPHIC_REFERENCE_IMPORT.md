# Geographic reference-data imports

GovConnectX accepts System Admin-only CSV imports for ward and community reference records.

## Required CSV format

UTF-8 CSV, maximum 2 MB and 5,000 data rows:

```csv
record_type,code,name,parent_code
ward,OFFICIAL-WARD-CODE,Official ward name,OFFICIAL-LGA-CODE
community,OFFICIAL-COMMUNITY-CODE,Official community name,OFFICIAL-WARD-CODE
```

- `record_type`: `ward` or `community`.
- Ward `parent_code`: an existing LGA code from the State/LGA reference directory.
- Community `parent_code`: an existing active ward code, or a ward included in the same CSV.
- Ward and community codes must be the actual codes used by the authoritative source.
- Duplicate codes, missing parents, inactive parent wards, malformed rows and conflicts with existing records block the entire import.
- Existing rows are never overwritten. Correct the source data or use a separately reviewed administrative change process for amendments.

## Import procedure

1. Obtain a source file from INEC or the relevant State/LGA authority. Confirm that it actually identifies the relevant administrative units and their parent relationships.
2. In the System Admin Command Centre, provide the publisher/source name, document or public reference, optional effective date, and CSV file.
3. Select **Validate and preview**. Review all row-level errors and correct the source file if any appear.
4. Select **Commit validated import** only when the preview is valid. The backend revalidates the file during commit; the preview alone does not write data.
5. Check the ward/community directory and the audit log after import.

## Provenance and safeguards

Each imported row stores source name, source reference, effective date, import timestamp and importing administrator. Public ward/community lookup responses expose the source name, reference and effective date. A separate append-only audit event records the batch summary.

The import is all-or-nothing: one invalid row prevents the whole batch from being committed. Existing records are not silently updated or deleted. Importing a record does not certify that its source is genuine; a System Admin must independently confirm the publisher and document before committing.

## Endpoints

- `POST /api/v1/locations/admin/import/preview` — multipart CSV validation, no writes.
- `POST /api/v1/locations/admin/import/commit` — revalidates and commits the complete batch.
- Both endpoints require the `system_admin` role and require `file`, `source_name`, and `source_reference` form fields. `effective_from` is optional.
