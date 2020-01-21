import math
from typing import Set, Optional
from splitter.enums import DictionarySource


def get_word_value(term: str = "", frequency: float = 1E-8, multiplier: float = 1.0, sources: Optional[Set] = None) -> float:
    """Special logic to determine the relative value of a term.  This was one of dozens of original algorithms
    and was selected as the primary scoring method after months of refinement."""
    if sources is None:
        sources = set()
    if frequency <= 0:
        frequency = 1E-8

    if ((len(term) <= 3) or ((" " in term) and (len(term) <= 4))) and (frequency > 0.001) and (DictionarySource.Supplemental not in sources):
        frequency = 1E-6
    if (len(term) <= 7) and (frequency > 0.001) and (" " in term) and (DictionarySource.Supplemental not in sources):
        frequency = 1E-6
    if (len(term) <= 7) and (" " in term) and (DictionarySource.Supplemental not in sources):
        frequency *= 0.001

    freq = frequency * 1E8
    log = math.log(freq)

    value = log * multiplier
    value *= float(len(term))
    return value
