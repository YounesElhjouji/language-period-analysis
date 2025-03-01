#!/usr/bin/env python3
"""Functions for extracting metadata from Shamela HTML files."""

import logging
import re
import uuid
from typing import Dict, Any, Union

from bs4 import BeautifulSoup, Tag, NavigableString

logger = logging.getLogger(__name__)

# Required metadata fields
REQUIRED_METADATA = {"book_name", "author", "section"}


class MetadataExtractionError(Exception):
    """Exception raised when required metadata cannot be extracted."""

    pass


def get_element_text(element: Union[Tag, NavigableString, None]) -> str:
    """Safely extract text from a BeautifulSoup element."""
    if element is None:
        return ""
    if isinstance(element, NavigableString):
        return element.strip()
    if isinstance(element, Tag):
        return element.get_text().strip()
    return ""


def has_class(element: Any, class_name: str) -> bool:
    """Check if an element has a specific class."""
    if not isinstance(element, Tag):
        return False

    classes = element.get("class", [])
    return class_name in classes if classes else False


def generate_book_id() -> str:
    """Generate a unique ID for a book."""
    return str(uuid.uuid4())


def extract_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract metadata from the first page of a Shamela HTML file.

    Args:
        soup: BeautifulSoup object of the HTML file

    Returns:
        dict: Metadata dictionary

    Raises:
        MetadataExtractionError: If first page with metadata cannot be found
    """
    metadata: Dict[str, Any] = {
        "book_name": None,
        "author": None,
        "author_death_year": None,
        "section": None,
        "book_id": generate_book_id(),
        "content_length": 0,  # Will be updated later
    }

    first_page = soup.select_one(".PageText")
    if not first_page:
        raise MetadataExtractionError("Could not find the first page with metadata")

    title_spans = first_page.find_all("span", class_="title")

    field_mapping = {
        "الكتاب": "book_name",
        "المؤلف": "author",
        "القسم": "section",
        "تحقيق": "editor",
        "الناشر": "publisher",
        "الطبعة": "edition",
        "عدد الصفحات": "pages",
        "تاريخ النشر": "publication_date",
    }

    for span in title_spans:
        field_text = span.get_text().strip()

        field_key = None
        for arabic_key, internal_key in field_mapping.items():
            if arabic_key in field_text:
                field_key = internal_key
                break

        if field_key is None:
            field_key = field_text

        if field_key == "author":
            author_parts = []
            current = span.next_sibling

            while current and not (
                isinstance(current, Tag) and current.name in ["span", "p"]
            ):
                if isinstance(current, NavigableString):
                    author_parts.append(current.strip())
                else:
                    author_parts.append(get_element_text(current))
                current = current.next_sibling

            author_text = " ".join(filter(None, author_parts))

            year_match = re.search(r"(\d+)", author_text)
            if year_match:
                metadata["author_death_year"] = year_match.group(1)

            cleaned_author = re.sub(r"\([^)]*\)", "", author_text).strip()
            metadata["author"] = cleaned_author
        else:
            next_element = span.next_sibling
            if next_element:
                element_text = get_element_text(next_element)

                if field_key == "pages":
                    num_match = re.search(r"(\d+)", element_text)
                    if num_match:
                        metadata[field_key] = num_match.group(1)
                    else:
                        metadata[field_key] = element_text
                else:
                    metadata[field_key] = element_text

    if not metadata["book_name"]:
        first_title = first_page.select_one(".title")
        if first_title:
            metadata["book_name"] = first_title.get_text().strip()

    missing_fields = [field for field in REQUIRED_METADATA if not metadata.get(field)]
    if missing_fields:
        logger.warning(f"Missing required metadata fields: {', '.join(missing_fields)}")

    return metadata


def update_content_length(metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
    """Update metadata with content length."""
    metadata["content_length"] = len(content)
    return metadata
