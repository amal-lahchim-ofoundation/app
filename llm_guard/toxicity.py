from llm_guard.input_scanners import Toxicity
from llm_guard.input_scanners.toxicity import MatchType

def toxic_scan(prompt):
    scanner = Toxicity(threshold=0.5, match_type=MatchType.SENTENCE)
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return sanitized_prompt, is_valid, risk_score

