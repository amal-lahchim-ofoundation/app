from llm_guard.input_scanners import Code

ALLOWED_LANGUAGES = [
    "Python", "JavaScript", "Java", "Go", "C++", "Ruby", "Rust", "C", "C#", "Perl", "PHP",
    "Kotlin", "Swift", "R", "Scala", "Mathematica", "Erlang", "Lua", "Fortran", "COBOL", 
    "Pascal", "AppleScript", "ARM Assembly", "PowerShell", "Visual Basic .NET", "jq"
]
IS_BLOCKED = True  
def scan_code(prompt):
    scanner = Code(languages=ALLOWED_LANGUAGES, is_blocked=IS_BLOCKED)
    sanitized_prompt, is_valid, risk_score = scanner.scan(prompt)
    return sanitized_prompt, is_valid, risk_score

