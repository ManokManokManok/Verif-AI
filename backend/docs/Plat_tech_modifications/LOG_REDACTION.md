# Log Redaction

The `SensitiveDataFilter` in `backend/src/infrastructure/logging/sensitive_filter.py`
reduces exposure of sensitive data in log messages. It applies regular-expression
patterns to string messages and string logging arguments, including patterns for
email addresses, passwords, bearer tokens, API keys, and MongoDB credentials.
Only formats matched by those patterns are redacted; the filter is not a guarantee
that logs contain no sensitive data.

## Configuration and limitations

`backend/verfai/settings.py` attaches the filter to its configured console and
security file handlers. The file handler is disabled when `LOG_TO_FILE=false`.
Other handlers or direct output such as `print()` and file writes may bypass it.
The filter does not redact exception traceback text, non-string arguments, or
arbitrary nested data automatically. Avoid logging sensitive data in the first
place, including in exceptions.

For structured data, `SensitiveDataFilter.redact_dict()` returns a copy with
matching sensitive keys redacted, including keys in nested dictionaries and
lists of dictionaries. For strings outside the logging handlers,
`redact_sensitive_data()` applies the same patterns manually. Both approaches
have limits and should be reviewed before output.

Redaction alone does not establish compliance with privacy or security standards.
Existing logs may contain data written before filtering or through other paths;
handle and review them according to the project's privacy practices.

## Testing

From `backend`, run:

```powershell
python -m pytest tests/test_log_redaction.py
```

Add focused tests when changing patterns or redaction behavior.
