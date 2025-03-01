"""Shamela HTML processing package."""

from shamela.content import (extract_content_from_file,
                             extract_content_from_files)
from shamela.metadata import MetadataExtractionError, extract_metadata
from shamela.processor import (process_multifile_book, process_path,
                               process_single_file)

__all__ = [
    "extract_metadata",
    "MetadataExtractionError",
    "extract_content_from_file",
    "extract_content_from_files",
    "process_path",
    "process_single_file",
    "process_multifile_book",
]
