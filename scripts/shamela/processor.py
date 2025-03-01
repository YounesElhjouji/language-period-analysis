#!/usr/bin/env python3
"""Functions for processing Shamela HTML files and directories."""

import json
import logging
import os
import re
from pathlib import Path
from typing import List

from bs4 import BeautifulSoup
from shamela.content import (extract_content_from_file,
                             extract_content_from_files)
from shamela.metadata import extract_metadata

logger = logging.getLogger(__name__)


def is_multifile_book(directory: str) -> bool:
    """
    Check if a directory contains a multi-file book.

    Args:
        directory: Path to the directory

    Returns:
        bool: True if the directory contains a multi-file book
    """
    if not os.path.isdir(directory):
        return False

    # Check for 000.htm file which is the first file in multi-file books
    if not os.path.exists(os.path.join(directory, "000.htm")):
        return False

    # Check for at least one more numbered HTML file
    files = os.listdir(directory)
    for file in files:
        if re.match(r"00[1-9]\.htm", file):
            return True

    return False


def get_book_files(directory: str) -> List[str]:
    """
    Get all HTML files for a book in correct order.

    Args:
        directory: Path to the directory containing the book files

    Returns:
        List[str]: List of file paths in correct order
    """
    files = []

    # Get all HTML files
    for file in os.listdir(directory):
        if file.endswith(".htm"):
            files.append(os.path.join(directory, file))

    # Sort files numerically
    files.sort(key=lambda x: int(os.path.basename(x).split(".")[0]))

    return files


def process_single_file(file_path: str, output_dir: str) -> bool:
    """
    Process a single HTML file.

    Args:
        file_path: Path to the HTML file
        output_dir: Directory to save output files

    Returns:
        bool: True if processing was successful
    """
    try:
        base_name = Path(file_path).stem

        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, "html.parser")
        metadata = extract_metadata(soup)
        body_text = extract_content_from_file(file_path)

        # Save metadata
        metadata_path = os.path.join(output_dir, f"{base_name}_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Save content
        text_path = os.path.join(output_dir, f"{base_name}_text.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(body_text)

        logger.info(f"Processed single file: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return False


def process_multifile_book(directory: str, output_dir: str) -> bool:
    """
    Process a multi-file book.

    Args:
        directory: Path to the directory containing the book files
        output_dir: Directory to save output files

    Returns:
        bool: True if processing was successful
    """
    try:
        book_files = get_book_files(directory)
        if not book_files:
            logger.error(f"No HTML files found in {directory}")
            return False

        # Extract metadata from first file
        first_file = book_files[0]
        with open(first_file, "r", encoding="utf-8") as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, "html.parser")
        metadata = extract_metadata(soup)

        # Extract content from all files
        body_text = extract_content_from_files(book_files)

        # Use directory name as base name
        base_name = os.path.basename(directory)

        # Save metadata
        metadata_path = os.path.join(output_dir, f"{base_name}_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Save content
        text_path = os.path.join(output_dir, f"{base_name}_text.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(body_text)

        logger.info(f"Processed multi-file book: {directory}")
        return True

    except Exception as e:
        logger.error(f"Error processing book directory {directory}: {str(e)}")
        return False


def process_path(path: str, output_dir: str) -> bool:
    """
    Process a path which could be a file or directory.

    Args:
        path: Path to process
        output_dir: Directory to save output files

    Returns:
        bool: True if processing was successful
    """
    if os.path.isfile(path) and path.endswith(".htm"):
        return process_single_file(path, output_dir)

    elif os.path.isdir(path):
        if is_multifile_book(path):
            return process_multifile_book(path, output_dir)
        else:
            # Process all HTML files and subdirectories
            success = True
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                item_output_dir = os.path.join(output_dir, item)

                if os.path.isdir(item_path):
                    os.makedirs(item_output_dir, exist_ok=True)
                    if not process_path(item_path, item_output_dir):
                        success = False

                elif item.endswith(".htm"):
                    if not process_single_file(item_path, output_dir):
                        success = False

            return success

    else:
        logger.warning(f"Skipping unsupported path: {path}")
        return False
