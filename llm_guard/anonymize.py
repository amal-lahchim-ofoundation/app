from llm_guard.input_scanners import Anonymize
from llm_guard.input_scanners.anonymize_helpers import BERT_LARGE_NER_CONF
from llm_guard.vault import Vault
vault = Vault()

def anonymize_text(prompt, allowed_names, hidden_names, preamble):
    scanner = Anonymize(
        vault,
        preamble=preamble,
        allowed_names=allowed_names,
        hidden_names=hidden_names,
        recognizer_conf=BERT_LARGE_NER_CONF,
        language="en"
    )
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return {
        "sanitized_prompt": sanitized_prompt,
        "is_valid": is_valid,
        "risk_score": risk_score
    }
