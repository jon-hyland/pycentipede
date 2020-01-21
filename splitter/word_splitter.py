from typing import List, Tuple, Set, Optional
from utils.extensions import has_numbers
from utils.extensions import has_alphas
from utils.extensions import is_integer
from utils.extensions import substring
from utils.extensions import remove
from utils.extensions import find_any
from utils.stopwatch import Stopwatch
from utils.service_stats import ServiceStats
from utils import error_handler
from splitter.dictionary import Dictionary
from splitter.cache import SplitCache
from splitter.term import Term
from splitter.split_pass import Pass
from splitter.split import Split
from splitter.split_result import SplitResult


class Splitter():
    
    def __init__(self, dictionary: Dictionary, cache: SplitCache, service_stats: Optional[ServiceStats]) -> None:
        """Class constructor."""
        self.__break_chars = [" ", "-", "_", ".", "!", "?", "@", "$", "&", "*", ",", "[", "]", "(", ")", "{", "}", ";", ":", "%", "^", "~"]
        self.__dictionary = dictionary
        self.__cache = cache
        self.__service_stats = service_stats

    def simple_split(self, input_: str, cache: bool, max_terms: int, max_passes: int, errors: List[Exception]) -> SplitResult:
        """Returns only the best split recommendation, using the default set of parameters."""
        try:
            # normalize input
            input_ = (input_ if input_ is not None else "").strip().lower()

            # try from cache
            if cache:
                result = self.__cache.get_item(input_)
            else:
                result = None        

            # no? perform split logic
            if result is None:
                result = self.full_split(input_, cache, 1, max_terms, max_passes, errors)

            # return
            return result

        except Exception as ex:
            errors.append(ex)
            error_handler.log_error(ex)


    def full_split(self, input_: str, cache: bool, pass_display: int, max_terms: int, max_passes: int, errors: List[Exception]) -> SplitResult:
        """Split the text using a single method and dictionary.  Will usually produce multiple passes (results).  Adds output to the cache."""
        sw = Stopwatch()
        try:
            # normalize input
            input_ = (input_ if input_ is not None else "").strip().lower()

            # execute split
            t = self.split_logic(input_, max_terms, max_passes)
            passes: List[Pass] = t[0]
            matched_terms: List[Term] = t[1]

            # truncate
            pass_count = len(passes)
            if len(passes) > pass_display:
                del passes[pass_display:]

            # create object
            result = SplitResult(input_, None, None, len(matched_terms), matched_terms, pass_count, passes, sw.elapsed_ms, False)

            # cache
            if cache:
                self.__cache.set_item(input_, result)

            # return
            return result

        except Exception as ex:
            errors.append(ex)
            error_handler.log_error(ex)

        finally:
            if self.__service_stats:
                self.__service_stats.log_operation(name="full_split", elapsed_ms=sw.elapsed_ms)


    def split_logic(self, input_: str, max_terms: int, max_passes: int) -> Tuple[List[Pass], List[Term]]:
        """Executes the primary split logic."""
        passes: List[Pass] = []
        unique_passes: Set[str] = set()

        # init passes
        first_pass = Pass(input_)
        passes.append(first_pass)

        # split on numbers, with special cases
        self.split_on_numbers(passes)

        # preserve strings like "a-1"
        self.preserve_a1(passes)

        # split on break chars
        self.split_on_break_chars(passes)

        # get small list of possible matching terms
        matched_terms: List[Term] = self.__dictionary.find_matching_terms(input_, 3)
        matched_terms.sort(key=lambda x: x.value(), reverse=True)
        if len(matched_terms) > max_terms:
            del matched_terms[max_terms:]

        # loop through each possible term
        for term in matched_terms:

            # loop through passes (we can add a pass to the end while iterating this loop)
            for pass_index in range(len(passes)):

                # get next pass
                pass_ = passes[pass_index]

                # skip if this one done
                if pass_.is_done():
                    continue

                # loop through this passes splits
                for split_index in range(len(pass_.splits)):

                    # not yet matched?
                    if not pass_.splits[split_index].matched:

                        # contains the current word?
                        if term.compressed in pass_.splits[split_index].text:

                            # clone this pass into a new pass, create the new split in the new pass
                            new_pass = pass_.clone()
                            start_index = new_pass.splits[split_index].text.find(term.compressed)
                            new_pass.split(split_index, start_index, len(term.compressed), term)

                            # decide if this pass is unique.. if so add it to passes
                            unique_string = new_pass.unique_string()
                            if unique_string not in unique_passes:
                                unique_passes.add(unique_string)
                                passes.append(new_pass)
                                if len(passes) > max_passes:
                                    break

                # break if we've hit max passes (prevent HUGE split times at expense of accuracy)
                if len(passes) > max_passes:
                    break

            # decide if we're done (no more unsplit passes)
            done = True
            for p in passes:
                done = p.is_done()
                if not done:
                    break

            # decide if we're done (limit number of passes)
            if len(passes) > max_passes:
                done = True

            # stop if done
            if done:
                break

        # try to match any remaining splits
        for p in passes:
            for s in p.splits:
                if not s.matched:
                    best_term = self.__dictionary.find_term(s.text)
                    if best_term is not None:
                        s.match(best_term)
                        p.generate_stored_values()
                    elif is_integer(s.text):
                        s.match_without_word()
                        p.generate_stored_values()

        # sort passes by calculated value
        passes.sort(key=lambda x: x.score(), reverse=True)

        # remove duplicates
        passes_copy = []
        unique = set()
        for p in passes:
            if p.display_text() not in unique:
                unique.add(p.display_text())
                passes_copy.append(p)
        passes = passes_copy

        # return
        return passes, matched_terms


    def split_on_numbers(self, passes: List[Pass]) -> None:
        """Split on numbers, with special cases."""
        new_passes: List[Pass] = []
        for pass_ in passes:
            # continue if empty input
            if not pass_.display_text():
                continue

            # continue if only one char
            if len(pass_.display_text()) == 1:
                continue

            # continue if no digits
            if not has_numbers(pass_.display_text()):
                continue

            # determine which characters are digits
            characters = pass_.display_text()
            char_is_number: List[bool] = []
            for i in range(len(characters)):
                char_is_number.append(False)
                c = characters[i]
                if has_numbers(c):
                    char_is_number[i] = True
                else:
                    char_is_number[i] = False

            # find special case values like '3d' and '80s', split them out as segments
            # that are not numeric (so they will be ignored in the following logic)
            for term in self.__dictionary.get_special_numbers():
                index = pass_.display_text().find(term.compressed)
                if index != -1:
                    for i in range(index, (index + len(term.compressed))):
                        char_is_number[i] = False

            # break input into segments of digits and non-digits
            segments: List[str] = []
            numeric_segments: List[bool] = []
            is_number = char_is_number[0]
            start_index = 0
            for i in range(1, len(characters)):
                if char_is_number[i] != is_number:
                    length = i - start_index
                    seg = substring(characters, start_index, length)
                    numeric_segment = False
                    for j in range(start_index, (start_index + length)):
                        if char_is_number[j]:
                            numeric_segment = True
                            break
                    start_index = i
                    is_number = char_is_number[i]
                    segments.append(seg)
                    numeric_segments.append(numeric_segment)
            length = len(characters) - start_index
            seg = substring(characters, start_index, length)
            numeric_segment2 = False
            for j in range(start_index, (start_index + length)):
                if char_is_number[j]:
                    numeric_segment2 = True
                    break
            segments.append(seg)
            numeric_segments.append(numeric_segment2)

            # special logic to consider string like "1st, 2nd, 3rd, 101st, 286192nd" as digit segments
            for i in range(len(segments) - 1):
                if numeric_segments[i]:
                    last_digit = segments[i][len(segments[i]) - 1]
                    last_two_digits = substring(segments[i], len(segments[i]) - 2) if len(segments[i]) > 1 else ""
                    ext = ""
                    if (last_digit == "4") or (last_digit == "5") or (last_digit == "6") or (last_digit == "7") \
                            or (last_digit == "8") or (last_digit == "9") or (last_digit == "0"):
                        ext = "th"
                    elif last_digit == "1":
                        ext = "st"
                    elif last_digit == "2":
                        ext = "nd"
                    elif last_digit == "3":
                        ext = "rd"
                    if (last_two_digits == "11") or (last_two_digits == "12") or (last_two_digits == "13"):
                        ext = "th"
                    if segments[i + 1].startswith(ext):
                        segments[i] = segments[i] + substring(segments[i + 1], 0, 2)
                        segments[i + 1] = remove(segments[i + 1], 0, 2)

            # convert segments to a new pass of splits
            splits: List[Split] = []
            for i in range(len(segments)):
                segment = segments[i]
                numeric_segment = numeric_segments[i]
                if not segment:
                    continue
                if numeric_segment:
                    term = self.__dictionary.find_term(segment)
                    if term is not None:
                        split = Split.from_term(term)
                        splits.append(split)
                    else:
                        splits.append(Split(segment, 1E-8, 1.0, True, set()))
                else:
                    splits.append(Split(segment, 1E-8, 1.0, False, set()))
            new_pass = Pass(pass_.display_text(), splits, None, None)
            new_passes.append(new_pass)

        # add new passes
        for pass_ in new_passes:
            passes.append(pass_)


    def preserve_a1(self, passes: List[Pass]) -> None:
        """Special logic to preserve the '-' in terms like "a-1" and combine them into a single unit.
        This is intended to run after the logic that splits numeric terms.  It will combine two split terms
        ("a-" and "1") into a single unit.  The first split in the pass needs to be a single alpha character
        followed by a dash.  The next split needs to be numeric only, of any size but with no letters."""
        new_passes: List[Pass] = []
        for pass_ in passes:
            if (len(pass_.splits) >= 2) and (len(pass_.splits[0].text) == 2) \
                    and (has_alphas(substring(pass_.splits[0].text, 0, 1))) \
                    and (substring(pass_.splits[0].text, 1, 1) == "-") \
                    and (has_numbers(pass_.splits[1].text)):
                text = pass_.splits[0].text + pass_.splits[1].text
                splits: List[Split] = []
                term = self.__dictionary.find_term(text)
                if term is not None:
                    split = Split.from_term(term)
                    splits.append(split)
                else:
                    split = Split(text, 1E-8, 1.0, True, set())
                    splits.append(split)
                if len(pass_.splits) > 2:
                    for i in range(2, len(pass_.splits)):
                        splits.append(pass_.splits[i])
                new_pass = Pass(pass_.input, splits, None, None)
                new_passes.append(new_pass)
        for pass_ in new_passes:
            passes.append(pass_)


    def split_on_break_chars(self, passes: List[Pass]) -> None:
        """Splits the initial pass into predetermined segments if the input contains characters like '-' and others."""
        new_passes: List[Pass] = []
        for pass_ in passes:
            split_required = False
            for split in pass_.splits:
                if (not split.matched) and (find_any(split.text, self.__break_chars) != -1):
                    split_required = True
            if split_required:
                splits: List[Split] = []
                for split in pass_.splits:
                    if split.matched or (find_any(split.text, self.__break_chars) == -1):
                        splits.append(split)
                    else:
                        s = split.text
                        for c in self.__break_chars:
                            if c in s:
                                s = s.replace(c, " ")
                        items = s.split(" ")
                        for item in items:
                            if item:
                                splits.append(Split(item))
                new_pass = Pass(pass_.input, splits, None, None)
                new_passes.append(new_pass)
        for pass_ in new_passes:
            passes.append(pass_)
