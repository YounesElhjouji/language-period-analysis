#!/usr/bin/env python3
"""
Script to collect first pages of books with missing metadata fields into a single HTML file.
"""

import argparse
import json
import logging
import os
from typing import Any, Dict, Set

import colorlog
from bs4 import BeautifulSoup

from shamela.metadata import REQUIRED_METADATA


def setup_logger(log_level=logging.INFO):
    """Set up a logger."""
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s%(reset)s - %(levelname_log_color)s%(levelname)s%(reset)s - %(message)s",
            log_colors={
                "DEBUG": "white",
                "INFO": "white",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
            secondary_log_colors={
                "levelname": {
                    "DEBUG": "white",
                    "INFO": "white",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "red,bold",
                }
            },
            style="%",
        )
    )

    logger = colorlog.getLogger()
    logger.setLevel(log_level)
    logger.handlers = []
    logger.addHandler(handler)
    return logger


def load_metadata_file(metadata_path: str) -> Dict[str, Any]:
    """Load metadata from file."""
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error loading metadata file: {str(e)}")
        return {}


def find_books_with_missing_metadata(metadata: Dict[str, Any]) -> Dict[str, Set[str]]:
    """Find books with missing metadata fields."""
    books_with_missing_fields = {}

    for book_id, book_metadata in metadata.items():
        missing_fields = {
            field for field in REQUIRED_METADATA if not book_metadata.get(field)
        }
        if missing_fields:
            books_with_missing_fields[book_id] = missing_fields

    return books_with_missing_fields


def find_html_file_for_book(book_name: str, input_dir: str) -> str:
    """Find the HTML file for a book by its name."""
    # Check for multi-file books first
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)

        if os.path.isdir(item_path):
            # Check for 001.htm file
            first_file = os.path.join(item_path, "001.htm")
            if os.path.exists(first_file):
                try:
                    with open(first_file, "r", encoding="utf-8") as f:
                        if book_name in f.read():
                            return first_file
                except Exception:
                    pass

    # Check for single HTML files
    for item in os.listdir(input_dir):
        if item.endswith(".htm"):
            file_path = os.path.join(input_dir, item)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    if book_name in f.read():
                        return file_path
            except Exception:
                pass

    return ""


def main():
    parser = argparse.ArgumentParser(
        description="Collect first pages of books with missing metadata fields"
    )
    parser.add_argument("metadata_file", help="Path to metadata.json file")
    parser.add_argument(
        "input_dir", help="Directory containing the original HTML files"
    )
    parser.add_argument("output_file", help="Path to save the combined HTML file")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )

    args = parser.parse_args()

    # Set up logger
    global logger
    logger = setup_logger(getattr(logging, args.log_level))

    # Load metadata
    logger.info(f"Loading metadata from {args.metadata_file}")
    metadata = load_metadata_file(args.metadata_file)

    if not metadata:
        logger.error("No metadata loaded. Exiting.")
        return

    # Find books with missing metadata
    logger.info("Identifying books with missing metadata fields")
    books_with_missing_fields = find_books_with_missing_metadata(metadata)

    if not books_with_missing_fields:
        logger.info("No books with missing metadata fields found.")
        return

    logger.info(
        f"Found {len(books_with_missing_fields)} books with missing metadata fields"
    )

    # Create a simple HTML file with all first pages
    html = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Books with Missing Metadata</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        .book {
            margin-bottom: 30px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 20px;
        }
        .book-info {
            margin-bottom: 10px;
            font-weight: bold;
        }
        .missing-fields {
            color: red;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
"""

    # Add each book's first page
    for book_id, missing_fields in books_with_missing_fields.items():
        book_metadata = metadata.get(book_id, {})
        book_name = book_metadata.get("book_name", "Unknown")

        html += f"""
<div class="book">
    <div class="book-info">Book: {book_name}</div>
    <div class="missing-fields">Missing fields: {', '.join(missing_fields)}</div>
"""

        # Find and add the original HTML content
        html_file = find_html_file_for_book(book_name, args.input_dir)
        if html_file:
            try:
                with open(html_file, "r", encoding="utf-8") as f:
                    soup = BeautifulSoup(f.read(), "html.parser")
                    first_page = soup.select_one(".PageText")
                    if first_page:
                        html += str(first_page)
                    else:
                        html += (
                            "<p>Could not find PageText element in the HTML file.</p>"
                        )
            except Exception as e:
                html += f"<p>Error loading HTML file: {str(e)}</p>"
        else:
            html += f"<p>Could not find HTML file for book: {book_name}</p>"

        html += "</div>\n"

    html += """
</body>
</html>
"""

    # Save the HTML file
    logger.info(f"Saving combined HTML to {args.output_file}")
    with open(args.output_file, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Done")


if __name__ == "__main__":
    main()
