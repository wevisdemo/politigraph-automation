from typing import List, Dict
import re

from .thai_name_prefixes import NAME_PREFIXES

NORMALIZE_NAME_PATTERN = [
    (r"(?<=[\u0e01-\u0e2e])(?P<Garrun>\u0e4c)(?P<Vowel>[\u0e34-\u0e39])", r"\g<Vowel>\g<Garrun>"),
    (r"เเ", r"แ")
]

def normalize_thai_name(name: str) -> str:
    # Normalize Thai vowel pattern
    normalized_name = name
    for pattern, repl in NORMALIZE_NAME_PATTERN:
        normalized_name = re.sub(pattern, repl, normalized_name)
    # Remove duplicated space
    normalized_name = re.sub(r"\s+", " ", normalized_name)
    return normalized_name

def remove_thai_name_prefix(name: str, prefixes:List[str]=[]) -> str:
    # Load & combine two set of prefixes
    master_prefixes_list = NAME_PREFIXES + prefixes
    # Remove prefix from name
    result_name = min(
        [re.sub(prefix, "", name).strip() for prefix in master_prefixes_list],
        key=len
    )
    # Normalize name
    result_name = normalize_thai_name(result_name)
    return result_name