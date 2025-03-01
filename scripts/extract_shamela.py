#!/usr/bin/env python3
"""
Script to extract metadata and content from Shamela HTML files.
Handles both single HTML files and multi-file books.
Generates a unique ID for each book and stores all metadata in a single file.
"""

import argparse
import logging
import os
import sys

from shamela.processor import process_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Extract metadata and content from Shamela HTML files"
    )
    parser.add_argument("input_path", help="Path to Shamela HTML file or directory")
    parser.add_argument(
        "-o", "--output_dir", help="Output directory for extracted data", required=True
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level",
    )

    args = parser.parse_args()

    # Set log level
    logger.setLevel(getattr(logging, args.log_level))

    # Create output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Process the input path
    try:
        success = process_path(args.input_path, output_dir)
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
