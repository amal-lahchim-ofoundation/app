from llm_guard.input_scanners import Gibberish
from llm_guard.input_scanners.gibberish import MatchType

def gibberish_scan(prompt):
    scanner = Gibberish(match_type=MatchType.FULL)
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return sanitized_prompt, is_valid, risk_score

