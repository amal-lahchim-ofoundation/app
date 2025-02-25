from llm_guard.input_scanners import BanTopics

TOPICS = ["politics", "violence"]
def topic_scan(prompt):
    scanner = BanTopics(topics=TOPICS, threshold=0.5)
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return sanitized_prompt, is_valid, risk_score

