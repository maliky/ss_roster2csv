# io_utils.py
"""
ss_roster2csv/io_utils.py

Provides I/O utilities for reading PDFs (via pdftotext) or 
reading the raw text roster (pages) from a text file. 
Skips lines containing certain strings, handles formfeed, etc.
"""

import os
import subprocess
import logging
from typing import List

# Configure logger
logger = logging.getLogger(__name__)


def line_of_interest(line: str) -> bool:
    """
    Determine if a line contains useful information for processing.

    Args:
        line (str): A line from the roster text file.

    Returns:
        bool: True if the line should be kept, False otherwise.
    """
    to_ignore_exactly = [
        "",
        "Roster",
        "Academic Yr.",
        "2024/2025",
        "Harper, Maryland County",
    ]
    to_be_contained = ["Smart School"]

    if line in to_ignore_exactly:
        logger.debug(f"Ignoring exact match: '{line}'")
        return False

    if any(skip in line for skip in to_be_contained):
        logger.debug(f"Ignoring line containing: '{line}'")
        return False

    return True


def convert_pdf_to_text(pdf_path: str) -> str:
    """
    Convert a PDF file to text using the 'pdftotext' command-line utility.

    Args:
        pdf_path (str): Path to the input PDF file.

    Returns:
        str: Path to the generated text file.

    Raises:
        FileNotFoundError: If the output file was not created successfully.
    """
    txt_path = pdf_path.rsplit(".", 1)[0] + "_tmp.txt"
    cmd = ["pdftotext", pdf_path, txt_path]

    logger.info(f"Starting PDF to text conversion: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        if not os.path.isfile(txt_path):
            raise FileNotFoundError(f"Failed to create text from PDF: {txt_path}")

        logger.info(f"PDF successfully converted -> {txt_path}")
        return txt_path

    except subprocess.CalledProcessError as e:
        logger.error(f"PDF conversion failed: {e}")
        raise


def read_roster(text_file: str = "roster_250303.txt") -> List[List[str]]:
    """
    Reads a text file line by line, extracting pages while skipping unwanted content.

    Args:
        text_file (str): The path to the roster text file.

    Returns:
        List[List[str]]: A list of pages, where each page is a list of lines.
    """
    logger.info(f"Reading roster file: {text_file}")
    
    pages: List[List[str]] = []
    page: List[str] = []
    total_lines = 0
    ignored_lines = 0

    try:
        with open(text_file, "r") as f:
            for line in f:
                total_lines += 1
                line = line.rstrip("\n")

                if line_of_interest(line):
                    if line.startswith("\x0c"):  # Page break detected
                        if page:
                            pages.append(page)
                            logger.info(f"Page {len(pages)} added with {len(page)} lines.")
                            page = []

                        # Ignore the page break itself and any attached header text
                        continue

                    page.append(line.strip(':'))  # we strip ':' from all and daytime
                else:
                    ignored_lines += 1

        # Add the last page if not empty
        if page:
            pages.append(page)
            logger.info(f"Final page {len(pages)} added with {len(page)} lines.")

        logger.info(f"Finished reading file: {total_lines} lines processed, {ignored_lines} ignored.")
        logger.info(f"Total pages extracted: {len(pages)}")

        return pages

    except FileNotFoundError:
        logger.error(f"Roster file not found: {text_file}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error while reading roster: {e}")
        raise

