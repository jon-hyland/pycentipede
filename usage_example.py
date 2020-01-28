"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

from splitter.dictionary import Dictionary
from splitter.cache import SplitCache
from splitter.word_splitter import Splitter


"""This example shows how to use the word splitting package outside of
the included Flask HTTP application, i.e., to use as an internal component 
of another program."""

__dictionary: Dictionary
__cache: SplitCache
__splitter: Splitter

def initialize():
    global __dictionary
    global __cache
    global __splitter

    __dictionary = Dictionary()
    __cache = SplitCache(max_cache_items=1000, cleanup_secs=60.0)
    __splitter = Splitter(dictionary=__dictionary, cache=__cache)
    __dictionary.load_data("dictionary.txt")


def split_some_stuff():
    result = __splitter.simple_split(input_="splitthistextintoseparatewords")
    print(f"input: {result.input},  output: {result.output},  confidence_score: {result.score}")

    result = __splitter.simple_split(input_="someotherstuff")
    print(f"input: {result.input},  output: {result.output},  confidence_score: {result.score}")

    result = __splitter.full_split(input_="blahblahblahletssplitthisup", pass_display=5)
    print(f"input: {result.input},  output: {result.output},  confidence_score: {result.score}")
    for i in range(0, len(result.passes)):
        print(f"    pass: {i},  output: {result.passes[i].output},  score: {result.passes[i].score()}")


if __name__ == "__main__":
    initialize()
    split_some_stuff()
