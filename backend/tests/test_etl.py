"""Tests for ETL (data ingestion) endpoints."""

# Test cases planned:
# - test_upload_csv: Upload valid CSV returns success
# - test_upload_excel: Upload valid XLSX returns success
# - test_upload_invalid_format: Unsupported extension returns 400
# - test_upload_unauthenticated: Missing token returns 401
# - test_clear_history: Deletes only current user's sales
# - test_clear_history_empty: No data returns success message
