from llm_guard.input_scanners import Secrets

# `REDACT_PARTIAL` will show only leading and trailing characters.
REDACT_PARTIAL = "partial"
#  `REDACT_ALL` will shadow the full secret.
REDACT_ALL = "all"
# `REDACT_HASH` will replace the full secret with its hashed value.
REDACT_HASH = "hash"
def secrets_scan(prompt):
    scanner = Secrets(redact_mode=REDACT_PARTIAL)
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return sanitized_prompt, is_valid, risk_score