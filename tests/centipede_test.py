import re
import random
from typing import List
from time import sleep
from service import word_splitter
from splitter.split_result import SplitResult
from splitter.split_cache import SplitCache


__words: List[List[str]] = []


def initialize():
    load_words()
    di.dictionary.load_data(config.data_file)


def load_words():
    print(" * Loading test words..")
    load_file("tests/random_text_1.txt")
    load_file("tests/random_text_2.txt")


def load_file(filename):
    global __words
    with open(filename, "r") as f:
        file_lines = f.readlines()
    for file_line in file_lines:
        lines = file_line.replace(",", ".").replace("-", ".").split(".")
        lines = list(filter(None, lines))
        for line in lines:
            words = re.split(r"\W+", line.lower())
            words = list(filter(None, words))
            if (len(words) > 0):
                __words.append(words)


initialize()


def test_cache_accuracy(total_iterations=10000, target_success_percent=100.0):
    """Tests the accuracy of the split cache, ensuring no key collisions or
    other issues."""
    print("\nTesting split cache accuracy..")
    
    # vars
    cache = SplitCache(max_cache_items=10000)
    cheat = {}
    total_operations = 0
    correct_operations = 0

    # seed random number generator
    random.seed()

    # loop through test iterations
    for _ in range(0, total_iterations):

        # generate random item
        while True:
            line_index = random.randint(0, len(__words) - 1)
            line = __words[line_index]
            first_word_index = random.randint(0, len(line) - 1)
            word_count = random.randint(2, 4)
            left = len(line) - first_word_index
            if (word_count > left):
                word_count = left
            if word_count >= 2:
                break
        value = ""
        for i in range(0, word_count):
            word = line[first_word_index + i]
            value += word
        key = value.replace(" ", "")
        if key in cheat:
            continue

        # store in cache
        cache.set_item(key, SplitResult(key, value))
        cheat[key] = value

        # fetch from cache
        result = cache.get_item(key)
        total_operations += 1
        
        # evaluate result
        if (result is not None) and (result.output == value):
            correct_operations += 1

    # do it all again
    for key in cheat.keys():

        # fetch from cache
        result = cache.get_item(key)
        total_operations += 1
        
        # evaluate result
        if (result is not None) and (result.output == cheat[key]):
            correct_operations += 1        

    # final assert
    success_percent = round((float(correct_operations) / float(total_operations)) * 100.0, 1)    
    print(f"OVERALL SUCCESS PERCENT: {success_percent} (target={target_success_percent})")
    assert success_percent >= target_success_percent


def test_cache_cleanup():
    """Tests the accuracy of the split cache, ensuring no key collisions or
    other issues."""
    print("\nTesting split cache cleanup..")
    
    # vars
    cache = SplitCache(max_cache_items=100, cleanup_secs=5)

    # seed random number generator
    random.seed()

    # loop through test iterations
    for _ in range(0, 10000):

        # generate random item
        while True:
            line_index = random.randint(0, len(__words) - 1)
            line = __words[line_index]
            first_word_index = random.randint(0, len(line) - 1)
            word_count = random.randint(2, 4)
            left = len(line) - first_word_index
            if (word_count > left):
                word_count = left
            if word_count >= 2:
                break
        value = ""
        for i in range(0, word_count):
            word = line[first_word_index + i]
            value += word
        key = value.replace(" ", "")

        # store in cache
        cache.set_item(key, SplitResult(key, value))
    
    # sleep, allow cleanup to occur
    sleep(6)   

    # final assert
    count = cache.count
    print(f"ITEMS IN CACHE: {count} (should be close to or exactly 90)")
    assert (count <= 100) and (count >= 90)


def test_split_accuracy(total_iterations=1000, target_success_percent=85.0):
    """Tests splitter for accuracy by running a number of samples through the splitter.
    Samples consist of 2-4 contiguous words taken from written samples of English text.
    The correct answer is stored, spaces removed from input, and splitter tested for 
    accuracy."""
    print("\nTesting word splitter accuracy..")
    
    # vars
    max_terms = config.default_max_terms
    max_passes = config.default_max_passes
    total_operations = 0
    correct_operations = 0
    
    # seed random number generator
    random.seed()

    # loop through test iterations
    for iteration_number in range(0, total_iterations):
        print(f"==================== test_split_accuracy ({iteration_number + 1}/{total_iterations}) ====================")

        # generate random query
        while True:
            line_index = random.randint(0, len(__words) - 1)
            line = __words[line_index]
            first_word_index = random.randint(0, len(line) - 1)
            word_count = random.randint(2, 4)
            left = len(line) - first_word_index
            if (word_count > left):
                word_count = left
            if word_count >= 2:
                break
        input_ = ""
        correct_answer = ""
        for i in range(0, word_count):
            word = line[first_word_index + i]
            input_ += word
            if i > 0:
                correct_answer += " "
            correct_answer += word
        print(f" Input: {input_}")
        print(f" Orig : {correct_answer}")
        
        # run split command
        errors = []
        result = word_splitter.full_split(input_, False, 1, max_terms, max_passes, errors)

        # evaluate response
        output = result.output or ""
        if output == correct_answer:
            success = True
            correct_operations += 1
        else:
            success = False
        total_operations += 1

        # print output
        print(f" Output: {output}")
        print(f" Success: {str(success).upper()}")

    # final assert
    success_percent = round((float(correct_operations) / float(total_operations)) * 100.0, 1)    
    print(f"OVERALL SUCCESS PERCENT: {success_percent} (target={target_success_percent})")
    assert success_percent >= target_success_percent

