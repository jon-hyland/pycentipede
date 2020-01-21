from typing import List
from service import error_handler
from service.json_writer import JsonWriter
from service.enums import VerbosityLevel
from service import config
from service.word_splitter import SplitResult
from service import di


def error(errors: List[Exception], command: str = "unknown") -> str:
    """Writes the standard JSON response for fatal error, if a more specific command handler was not reached."""
    try:
        w = JsonWriter()
        w.write_start_object()
        __write_info(w, command, 0)
        __write_errors(w, errors)
        w.write_end_object()
        json = w.to_string()
        return json
    except Exception as ex:
        error_handler.log_error(ex)
        return ""


def get_stats() -> str:
    """Writes response for the 'getstats' command."""
    writer = JsonWriter()
    writer.write_start_object()
    __write_info(writer, "getstats")
    di.service_state.write_runtime_statistics(writer)
    di.split_cache.write_runtime_statistics(writer)
    di.service_stats.write_runtime_statistics(writer)
    writer.write_end_object()
    json = writer.to_string()
    return json


def word_split(verbosity: VerbosityLevel, inputs: List[str], pass_display: int, exhaustive: bool, results: List[SplitResult], elapsed: int, errors: List[Exception]) -> str:
    """Writes response for the 'wordsplit' command."""
    writer = JsonWriter()
    writer.write_start_object()
    __write_info(writer, "wordsplit", elapsed)
    writer.write_start_object("input")
    writer.write_property_value("input", ", ".join(inputs))
    writer.write_property_value("passdisplay", str(pass_display))
    writer.write_property_value("exhaustive", "1" if exhaustive else "0")
    writer.write_property_value("verbosity", str(int(verbosity)) + " (" + str(verbosity) + ")")
    writer.write_end_object()
    writer.write_start_array("output")
    for r in results:
        if verbosity is VerbosityLevel.Low:
            writer.write_start_object()
            writer.write_property_value("input", r.input)
            writer.write_property_value("output", r.output)
            writer.write_property_value("score", round(r.score, 2))
            writer.write_end_object()
        elif verbosity is VerbosityLevel.Medium:
            writer.write_start_object()
            writer.write_property_value("input", r.input)
            writer.write_property_value("output", r.output)
            writer.write_property_value("score", round(r.score, 2))
            writer.write_property_value("termCount", r.term_count)
            writer.write_property_value("passCount", r.pass_count)
            writer.write_property_value("elapsedMS", round(r.elapsed_ms, 0))
            writer.write_end_object()
        elif verbosity is VerbosityLevel.High:
            terms = ""
            if r.matched_terms:
                for t in r.matched_terms:
                    if len(terms) > 0:
                        terms += ", "
                    terms += t.full
            writer.write_start_object()
            writer.write_property_value("input", r.input)
            writer.write_property_value("output", r.output)
            writer.write_property_value("score", round(r.score, 2))
            writer.write_property_value("termCount", r.term_count)
            writer.write_property_value("passCount", r.pass_count)
            writer.write_property_value("elapsedMS", int(round(r.elapsed_ms, 0)))
            writer.write_property_value("terms", terms)
            writer.write_start_array("passes")
            if r.passes:
                for p in r.passes:
                    writer.write_start_object()
                    writer.write_property_value("text", p.display_text())
                    writer.write_property_value("score", round(p.score(), 2))
                    writer.write_end_object()
            writer.write_end_array()
            writer.write_end_object()
    writer.write_end_array()
    __write_errors(writer, errors)
    writer.write_end_object()
    json = writer.to_string()
    return json


def __write_info(writer: JsonWriter, command: str = "", elapsed: int = 0) -> None:
    """Writes standard 'info' node for many command responses."""
    writer.write_start_object("info")
    writer.write_property_value("serviceName", "PyCentipede")
    writer.write_property_value("version", config.version)
    writer.write_property_value("instanceName", config.instance_name)
    writer.write_property_value("command", command)
    writer.write_property_value("elapsedMs", int(round(elapsed, 0)))
    writer.write_end_object()


def __write_errors(writer: JsonWriter, errors: List[Exception]) -> None:
    """Writes standard 'errors' node for most command responses."""
    writer.write_start_array("errors")
    for ex in errors:
        writer.write_start_object()
        writer.write_start_array("args")
        for a in ex.args:
            writer.write_value(a)
        writer.write_end_array()
        writer.write_end_object()
    writer.write_end_array()
