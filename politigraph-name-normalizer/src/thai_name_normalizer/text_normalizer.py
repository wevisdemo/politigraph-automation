def convert_thai_number_str_to_arabic(thai_string: str) -> str:
    """
    Converts a string containing Thai numerals to Arabic numerals.

    This function takes a string that may contain Thai numerals (๐-๙) and
    translates them into their corresponding Arabic numeral (0-9) equivalents.
    Other characters in the string remain unchanged.

    Args:
    thai_string: The input string to be converted.

    Returns:
    A new string with all Thai numerals converted to Arabic numerals.
    """
    thai_to_arabic_map = str.maketrans('๐๑๒๓๔๕๖๗๘๙', '0123456789')
    return thai_string.translate(thai_to_arabic_map)