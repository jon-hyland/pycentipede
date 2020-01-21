from typing import List
import re


def substring(string: str, start_index: int, length: int = None) -> str:
    """
    Mimics the String.SubString(startIndex, length=null) function from C# (and other languages).
    Helpful for porting C# to Python, for readability since [:] (slice) works differently.
    :param string: The input string.
    :param start_index: The character index to start at.
    :param length: Optional length of character string to grab.
    :return: The sliced substring.
    """
    if length is None:
        sub = string[start_index:]
    else:
        sub = string[start_index:(start_index + length)]
    return sub


def has_numbers(string: str) -> bool:
    """
    Uses fast regular expression matching to return true if string contains any digit chars (0-9).
    :param string: The input string.
    :return: True if input contains one or more numeric characters.
    """
    exists = bool(re.search(r"\d", string))
    return exists


def is_integer(string: str) -> bool:
    """
    Tries to parse string as integer, returning true on success.
    :param string: The input string.
    :return: True if input is an integer.
    """
    try:
        int(string)
        return True
    except ValueError:
        return False


def has_alphas(string: str) -> bool:
    """
    Uses fast regular expression matching to return true if string contains any letter chars (a-z, A-Z).
    :param string: The input string.
    :return: True if input contains one or more alphabetic characters.
    """
    exists = bool(re.search(r"\w", string))
    return exists


def remove(string: str, start_index: int, count: int = 0) -> str:
    """
    Returns new string where certain number of characters starting at specified index are removed.
    :param string: The input string.
    :param start_index: The starting index to begin removing characters.
    :param count: The number of characters to remove.
    :return:
    """
    before = substring(string, 0, start_index)
    after = substring(string, (start_index + count))
    removed = before + after
    return removed


def find_any(string: str, match_list: List[str]) -> int:
    """
    Returns index of first match in match list, or -1 if no matches found.
    :param string: The input string.
    :param match_list: List of strings to match within the input string.
    :return: The starting index of the first match.  -1 if no matches are found.
    """
    for m in match_list:
        index = string.find(m)
        if index != -1:
            return index
    return -1
