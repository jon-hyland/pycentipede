"""PyCentipede - A Python-based word splitter
Copyright (C) 2019-2020  John Hyland
GNU GENERAL PUBLIC LICENSE Version 3"""

from flask import render_template, request, Response
from utils import error_handler
from utils.extensions import remove
from utils.stopwatch import Stopwatch
from service.command_writer import VerbosityLevel
from service import command_writer
from service import config
from service import app
from service import di


@app.route("/")
@app.route("/index")
@app.route("/index.htm")
@app.route("/index.html")
def index():
    """Renders and returns the index-page HTML template."""
    sw = Stopwatch()
    try:
        return render_template("index.html")
    except Exception as ex:
        error_handler.log_error(ex)
        return str(ex)
    finally:
        di.service_stats.log_command(name="index", elapsed_ms=sw.elapsed_ms)


@app.route("/ping")
def ping() -> Response:
    """Returns the plain text "Up", "LoadingData", or "Down" depending on service state."""
    sw = Stopwatch()
    try:
        response = di.service_state.state.name
    except Exception as ex:
        error_handler.log_error(ex)
        response = str(ex)
    finally:
        di.service_stats.log_command(name="ping", elapsed_ms=sw.elapsed_ms)
    return Response(response=response, mimetype="text/plain")


@app.route("/getstats")
def get_stats() -> Response:
    """Generates service statistics and returns JSON response."""
    errors = []
    sw = Stopwatch()
    try:
        response = command_writer.get_stats()
    except Exception as ex:
        errors.append(ex)
        error_handler.log_error(ex)
        response = command_writer.error(errors, "getstats")
    finally:
        di.service_stats.log_command(name="getstats", elapsed_ms=sw.elapsed_ms)
    return Response(response, mimetype="application/json")


@app.route("/wordsplit")
def word_split() -> Response:
    """Performs word split operation, returns JSON response with metadata OR plain text."""
    errors = []
    output = "json"
    sw = Stopwatch()
    try:
        # parse params
        inputs = (request.args.get("input") or "").replace("|", ",").split(",")
        pass_display = int(request.args.get("passdisplay") or "5")
        exhaustive = (request.args.get("exhaustive") or "0") == "1"
        verbosity = VerbosityLevel(int(request.args.get("verbosity") or "0"))
        output = (request.args.get("output") or "json").lower()
        cache = (request.args.get("cache") or "1") == "1"

        # parse restrictions
        if not exhaustive:
            max_input_chars = config.default_max_input_chars
            max_terms = config.default_max_terms
            max_passes = config.default_max_passes
        else:
            max_input_chars = config.exhaustive_max_input_chars
            max_terms = config.exhaustive_max_terms
            max_passes = config.exhaustive_max_passes

        # limit input
        for i in range(len(inputs)):
            if len(inputs[i]) > max_input_chars:
                inputs[i] = remove(inputs[i], max_input_chars)
        if len(inputs) > 1000:
            del inputs[1000:]

        # perform splits
        results = []
        for i in inputs:
            if (verbosity < VerbosityLevel.High) and (not exhaustive):
                result = di.word_splitter.simple_split(i, cache, max_terms, max_passes, errors)
            else:
                result = di.word_splitter.full_split(i, cache, pass_display, max_terms, max_passes, errors)
            results.append(result)
        
        # write response
        response = ""
        if output == "json":
            response = command_writer.word_split(verbosity, inputs, pass_display, exhaustive, results, sw.elapsed_ms, errors)
        elif output == "text":
            for r in results:
                response += r.output + "\n"

    except Exception as ex:
        errors.append(ex)
        error_handler.log_error(ex)
        response = command_writer.error(errors, "wordsplit")

    finally:
        di.service_stats.log_command(name="wordsplit", elapsed_ms=sw.elapsed_ms)

    return Response(response, mimetype="application/json" if output == "json" else "text/plain")
