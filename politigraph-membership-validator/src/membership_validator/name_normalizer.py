import re

NORMALIZE_NAME_PATTERN = [
    (r"(?<=[\u0e01-\u0e2e])(?P<Garrun>\u0e4c)(?P<Vowel>[\u0e34-\u0e39])", r"\g<Vowel>\g<Garrun>")
]

def normalize_thai_name(name: str) -> str:
    normalized_name = name
    for pattern, repl in NORMALIZE_NAME_PATTERN:
        normalized_name = re.sub(pattern, repl, normalized_name)
    
    return normalized_name