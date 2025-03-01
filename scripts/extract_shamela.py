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

import colorlog

from shamela.processor import process_path


# Configure subtle colorized logging
def setup_logger(log_level=logging.INFO):
    """Set up a subtly colorized logger with mostly white text"""
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
    logger.handlers = []  # Remove any existing handlers
    logger.addHandler(handler)
    return logger


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

    # Set up colorized logger
    logger = setup_logger(getattr(logging, args.log_level))

    # Create output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Process the input path
    try:
        logger.info(f"Processing input path: {args.input_path}")
        success = process_path(args.input_path, output_dir)
        if success:
            logger.info("Processing completed successfully")
        else:
            logger.error("Processing failed")
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
