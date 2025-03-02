#!/usr/bin/env python3
"""Functions for processing Shamela HTML files and directories."""

import json
import logging
import os
import re
import traceback
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from shamela.content import (extract_content_from_file,
                             extract_content_from_files)
from shamela.metadata import extract_metadata, update_content_length

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

    # Check for 001.htm file which is the first file in multi-file books
    if not os.path.exists(os.path.join(directory, "001.htm")):
        return False

    # Check for at least one more numbered HTML file
    files = os.listdir(directory)
    for file in files:
        if re.match(r"00[2-9]\.htm", file):
            return True

    return False


def filter_numeric_files(files: List[str]) -> List[str]:
    """
    Filter files to keep only those with numeric filenames and sort them.

    Args:
        files: List of file paths

    Returns:
        List of sorted file paths with numeric filenames
    """
    numeric_files = []
    ignored_files = []

    for file_path in files:
        basename = os.path.basename(file_path).split(".")[0]
        if basename.isdigit():
            numeric_files.append((int(basename), file_path))
        else:
            ignored_files.append(file_path)

    # Log warning for ignored files
    if ignored_files:
        ignored_file_names = []
        for filepath in ignored_files:
            ignored_file_names.append(os.path.basename(filepath))
        logger.warning(
            f"Ignored {len(ignored_files)} files that don't have numeric filenames "
            f"(showing first 10): {', '.join(ignored_file_names[:10])}"
        )

    # Sort by numeric value and return just the file paths
    numeric_files.sort()
    return [file_path for _, file_path in numeric_files]


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

    # Filter and sort files
    return filter_numeric_files(files)


def load_metadata_file(output_dir: str) -> Dict[str, Any]:
    """
    Load existing metadata file or create a new one.

    Args:
        output_dir: Directory where metadata file is stored

    Returns:
        Dict: Metadata dictionary
    """
    metadata_path = os.path.join(output_dir, "metadata.json")

    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not parse existing metadata file. Creating new one.")
            return {}

    return {}


def save_metadata_file(metadata: Dict[str, Any], output_dir: str) -> None:
    """
    Save metadata to file.

    Args:
        metadata: Metadata dictionary
        output_dir: Directory to save metadata file
    """
    metadata_path = os.path.join(output_dir, "metadata.json")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


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
        # Load existing metadata
        all_metadata = load_metadata_file(output_dir)

        with open(file_path, "r", encoding="utf-8") as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, "html.parser")
        book_metadata = extract_metadata(soup)
        book_id = book_metadata["book_id"]

        # Extract content
        body_text = extract_content_from_file(file_path)

        # Update content length
        book_metadata = update_content_length(book_metadata, body_text)

        # Save content
        text_path = os.path.join(output_dir, f"{book_id}.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(body_text)

        # Add to metadata collection
        all_metadata[book_id] = book_metadata
        save_metadata_file(all_metadata, output_dir)

        logger.debug(f"Processed single file: {file_path} -> {book_id}")
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
        # Load existing metadata
        all_metadata = load_metadata_file(output_dir)

        book_files = get_book_files(directory)
        if not book_files:
            logger.error(f"No HTML files found in {directory}")
            return False

        # Extract metadata from first file
        first_file = book_files[0]
        with open(first_file, "r", encoding="utf-8") as file:
            html_content = file.read()

        soup = BeautifulSoup(html_content, "html.parser")
        book_metadata = extract_metadata(soup)
        book_id = book_metadata["book_id"]

        # Extract content from all files
        body_text = extract_content_from_files(book_files)

        # Update content length
        book_metadata = update_content_length(book_metadata, body_text)

        # Save content
        text_path = os.path.join(output_dir, f"{book_id}.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(body_text)

        # Add to metadata collection
        all_metadata[book_id] = book_metadata
        save_metadata_file(all_metadata, output_dir)

        logger.debug(f"Processed multi-file book: {directory} -> {book_id}")
        return True

    except Exception as e:
        print(e)
        traceback.print_exc()
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

                if os.path.isdir(item_path):
                    if not process_path(item_path, output_dir):
                        success = False

                elif item.endswith(".htm"):
                    if not process_single_file(item_path, output_dir):
                        success = False

            return success

    else:
        logger.warning(f"Skipping unsupported path: {path}")
        return False
