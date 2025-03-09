"""
ss_roster2csv/cli.py

Implements the command-line interface. 
Parses arguments (--input-file, --output-file, --debug), calls 
the parser logic, and saves the final CSV.
"""

import argparse
import logging
import sys
from . import io_utils, parser
from .logging_config import setup_logging

logger = logging.getLogger(__name__)


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
        "--debug",
        dest="error_level",
        default="WARNING",
        help="Set logging level (e.g. DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    args = parser_cli.parse_args()

    # Setup logging based on debug level
    setup_logging(args.error_level)

    # Distinguish PDF vs text by file extension or other logic
    if args.input_file.lower().endswith(".pdf"):

        text_path = io_utils.convert_pdf_to_text(args.input_file)
    else:
        text_path = args.input_file

    # Read lines from the text file
    pages = io_utils.read_roster(text_path)

    # Build the list of 'courses'
    courses = parser.find_course_pages(pages)

    # Extract (header, students) pairs
    crs_data = parser.get_courses_info(courses)

    # Build the final DataFrame
    df = parser.build_long_table(crs_data)

    # Save to CSV
    df.to_csv(args.output_file, index=False)
    logger.info("Roster saved to: %s", args.output_file)
