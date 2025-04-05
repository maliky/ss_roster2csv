"""
ss_roster2csv/logging_config.py

Sets up the logging configuration and log level based on the '--debug' argument. 
"""


import logging


def setup_logging(error_level: str = "WARNING") -> None:
    """
    Configure logging for the ss_roster2csv application.
    error_level should be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL
    """
    numeric_level = getattr(logging, error_level.upper(), logging.WARNING)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
