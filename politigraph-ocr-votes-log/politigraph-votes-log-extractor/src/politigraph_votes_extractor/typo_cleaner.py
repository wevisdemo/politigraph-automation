from rapidfuzz import process, fuzz

from .politigraph_data_loader import get_politician_names, get_politocal_party_names

def correct_typo(
    typo_text: str, 
    correct_texts_list: list, 
    similarity_threshold:int=95
):
    """
    Corrects a Thai typo based on a list of correct texts using rapidfuzz.
    """
    # Use process.extractOne to find the best match
    best_match = process.extractOne(
        query=typo_text,
        choices=correct_texts_list,
        scorer=fuzz.WRatio,
        score_cutoff=similarity_threshold
    )

    # extractOne returns None if no match exceeds the score_cutoff
    if best_match:
        # best_match is a tuple: (matched_string, score, index_in_list)
        corrected_text = best_match[0]
        # print(f"Input: '{typo_text}' -> Matched: '{corrected_text}' with score: {best_match[1]}")
        return corrected_text
    else:
        # No match above the threshold, return the original text
        return typo_text
    
def is_header_valid(
    row: list, 
    column_header: list = ["ลําดับที่", "เลขที่บัตร", "ชื่อ - สกุล", "ชื่อสังกัด", "ผลการลงคะแนน"]
):
    for idx, text in enumerate(row):
        if fuzz.ratio(text, column_header[idx]) > 95:
            return True
    return False