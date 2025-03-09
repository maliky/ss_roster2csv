# io_utils.py
"""
ss_roster2csv/io_utils.py

Provides I/O utilities for reading PDF (via pdftotext) or 
reading the raw text roster (pages) from a text file. 
Skips lines containing certain strings, handles formfeed, etc.
"""

import os
import subprocess
import tempfile
import logging
from typing import List

logger = logging.getLogger(__name__)


def line_of_interest(line):
    """
    return if a line is deemed usefull for our purpose
    """
    to_ignore_exactly = [
        "",
        "Roster",
        "Academic Yr.",
        "2024/2025",
        "Harper, Maryland County",
    ]
    to_be_contained = ["Smart School"]
    return (not line in to_ignore_exactly) and ("Smart School" not in line)


def convert_pdf_to_text(pdf_path: str) -> str:
    """
    Convert a PDF file to text using the 'pdftotext' command-line utility.

    Args:
      pdf_path (str): Path to the input PDF file.
      txt_path (str): Path where the resulting .txt file will be saved.

    Raises:
      FileNotFoundError: If the output file was not created successfully.
    """
    txt_path =  pdf_path.split('.')[0] + "_tmp.txt"
    cmd = ["pdftotext", pdf_path, txt_path]
    logging.info(f"[INFO] Converting PDF to text:\n   {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    if not os.path.isfile(txt_path):
        raise FileNotFoundError(f"Failed to create text from PDF: {txt_path}")
    logging.info(f"[INFO] PDF converted successfully -> {txt_path}")
    return txt_path


def read_roster(text_file: str = "roster_250303.txt") -> List[List[str]]:
    """
    Read a text file line by line and return a list of non-empty lines,
    skipping lines containing 'Smart School' or pure newlines.

    Args:
        text_file (str): The path to the roster text file.

    Returns:
        List[str]: A list of stripped lines from the file.
    """
    pages: List[List[str]] = []
    page: List[str] = []

    with open(text_file, "r") as f:
        while True:
            line = f.readline()
            if not line:
                break
            line = line.rstrip("\n")
            if line_of_interest(line):
                if line.startswith("\x0c"):  #  page break
                    # make sur to add a page break for the first page
                    if page:
                        # Save existing page and start a new one
                        pages.append(page)
                        page = []
                        # we remove the page break and the 'William V.S. Tubman University'
                        # attached to it, we can ignore it
                        # line = line.lstrip("\x0c")
                else:
                    page.append(line)
    return pages
