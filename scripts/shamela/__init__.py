"""Shamela HTML processing package."""

from shamela.metadata import extract_metadata, MetadataExtractionError, generate_book_id
from shamela.content import extract_content_from_file, extract_content_from_files
from shamela.processor import process_path, process_single_file, process_multifile_book

__all__ = [
    "extract_metadata",
    "MetadataExtractionError",
    "generate_book_id",
    "extract_content_from_file",
    "extract_content_from_files",
    "process_path",
    "process_single_file",
    "process_multifile_book",
]
