from typing import List
from rapidfuzz import fuzz, distance

def correct_typo(
    typo_text: str,
    correct_texts_list: List[str],
    similarity_threshold: int = 90
) -> str:
    """
    Corrects a Thai typo based on a list of correct texts using Levenshtein distance.
    """
    
    if not correct_texts_list:
        return typo_text
    
    best_match = typo_text
    least_distance = float('inf')
    for correct_text in correct_texts_list:
        # Calculate Levenshtein distance
        dist = distance.Levenshtein.distance(typo_text, correct_text)
        # If the distance is less than the threshold, consider it a match
        if dist < least_distance:
            least_distance = dist
            best_match = correct_text
            if dist <= 1:
                break
    # Calculate character distance threshold
    char_distance_threshold = max(
        round(len(typo_text.replace(" ", "").strip()) * (100 - similarity_threshold) / 100),
        2 # Ensure at least 2 character difference
    )
    # If the best match is within the similarity threshold, return it
    if least_distance <= char_distance_threshold:
        return best_match
    else:
        return typo_text
    
def is_header_valid(
    row: list, 
    column_header: list = ["ลําดับที่", "เลขที่บัตร", "ชื่อ - สกุล", "ชื่อสังกัด", "ผลการลงคะแนน"]
):
    for idx, text in enumerate(row):
        if fuzz.ratio(text, column_header[idx]) > 95:
            return True
    return False