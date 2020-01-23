"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

import yaml

version: str = "2.1.0"
instance_name: str = ""
dev_listen_port: int = 5000
data_file: str = ""
default_max_input_chars: int = 100
default_max_terms: int = 25
default_max_passes: int = 10000
exhaustive_max_input_chars: int = 250
exhaustive_max_terms: int = 50
exhaustive_max_passes: int = 25000
max_cache_items: int = 100000


def load_settings():
    """Loads config settings from file."""
    global instance_name
    global dev_listen_port
    global data_file
    global default_max_input_chars
    global default_max_terms
    global default_max_passes
    global exhaustive_max_input_chars
    global exhaustive_max_terms
    global exhaustive_max_passes
    global max_cache_items

    print(" * Reading configuration file..")
    f = open("config.yml")
    settings = yaml.safe_load(f)
    f.close()
    instance_name = settings["service"]["instance_name"]
    dev_listen_port = settings["service"]["dev_listen_port"]
    data_file = settings["splitter"]["data_file"]
    default_max_input_chars = settings["splitter"]["default"]["max_input_chars"]
    default_max_terms = settings["splitter"]["default"]["max_terms"]
    default_max_passes = settings["splitter"]["default"]["max_passes"]
    exhaustive_max_input_chars = settings["splitter"]["exhaustive"]["max_input_chars"]
    exhaustive_max_terms = settings["splitter"]["exhaustive"]["max_terms"]
    exhaustive_max_passes = settings["splitter"]["exhaustive"]["max_passes"]
    max_cache_items = settings["splitter"]["max_cache_items"]


load_settings()
