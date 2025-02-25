from llm_guard.input_scanners import PromptInjection
from llm_guard.input_scanners.prompt_injection import MatchType

def injection_scan(prompt):
    scanner = PromptInjection(threshold=0.5, match_type=MatchType.FULL)
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return sanitized_prompt, is_valid, risk_score

