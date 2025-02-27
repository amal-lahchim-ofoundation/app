from llm_guard.input_scanners import Language
from llm_guard.input_scanners.language import MatchType

def language_scan(prompt):
    scanner = Language(valid_languages=["en", "de"], match_type=MatchType.FULL)
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return sanitized_prompt, is_valid, risk_score
