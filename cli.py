"""
ss_roster2csv/cli.py

Implements the command-line interface.
Parses arguments (--input-file, --output-file, --debug), 
calls the parser logic via process_roster(), and saves the final CSV.
"""

import argparse
import logging
import sys
import pandas as pd
from . import io_utils, parser
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


def process_roster(input_path: str) -> pd.DataFrame:
    """
    Processes a TU roster file (PDF or text) and returns a DataFrame.

    Args:
        input_path (str): Path to the input roster file (.pdf or .txt).

    Returns:
        pd.DataFrame: The parsed roster in long-table format.
    """

    # Convert PDF if necessary
    if input_path.lower().endswith(".pdf"):
        logger.info("Converting PDF to text: %s", input_path)
        text_path = io_utils.convert_pdf_to_text(input_path)
    else:
        text_path = input_path

    # Read lines from the text file
    pages = io_utils.read_roster(text_path)
    logger.info("Loaded %d pages from %s", len(pages), text_path)

    # Build the list of 'courses'
    courses = parser.find_course_pages(pages)
    logger.info("Extracted %d courses", len(courses))

    # Extract (header, students) pairs
    crs_data = parser.get_courses_info(courses)
    logger.info("Extracted headers & student data for %d courses", len(crs_data))

    # Build the final DataFrame
    df = parser.build_long_table(crs_data)
    logger.info("Final DataFrame with %d rows", len(df))

    return df


def main():
    """Entry point for the ss_roster2csv CLI."""
    parser_cli = argparse.ArgumentParser(
        description="Convert a TU roster PDF or text file into CSV."
    )
    parser_cli.add_argument(
        "--input-file",
        "-i",
        required=True,
        help="Path to the input PDF or text file (roster).",
    )
    parser_cli.add_argument(
        "--output-file", "-o", required=True, help="Path to the resulting CSV file."
    )
    parser_cli.add_argument(
        "--logging",
        "-l",
        dest="error_level",
        default="INFO",
        help="Set logging level (e.g. DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    args = parser_cli.parse_args()

    # Setup logging based on debug level
    setup_logging(args.error_level)

    try:
        df = process_roster(args.input_file)
        df.to_csv(args.output_file, index=False)
        logger.info("Roster saved to: %s", args.output_file)

    except Exception as e:
        logger.error("Failed to process roster: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
