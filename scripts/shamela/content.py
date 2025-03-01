#!/usr/bin/env python3
"""Functions for extracting content from Shamela HTML files."""

import re
from typing import List

from bs4 import BeautifulSoup, Tag, NavigableString

from shamela.metadata import has_class


def extract_page_content(page: Tag) -> str:
    """Extract text content from a single page."""
    page_text = ""

    for element in page.children:
        if isinstance(element, Tag) and has_class(element, "PageHead"):
            continue

        if (
            isinstance(element, Tag)
            and element.name == "span"
            and has_class(element, "title")
        ):
            title_text = element.get_text().strip()
            if title_text:
                page_text += f"\n## {title_text}\n"
            continue

        if isinstance(element, Tag) and element.name == "p":
            p_text = element.get_text().strip()
            if p_text:
                page_text += p_text + "\n"
            continue

        if isinstance(element, NavigableString) and element.strip():
            text = element.strip()
            if text:
                page_text += text + "\n"

    return page_text


def clean_text(text: str) -> str:
    """Clean up extracted text."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("…", "...")
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]", "", text)
    return text.strip()


def extract_content_from_soup(soup: BeautifulSoup, skip_first_page: bool = True) -> str:
    """
    Extract content from a BeautifulSoup object.

    Args:
        soup: BeautifulSoup object of the HTML file
        skip_first_page: Whether to skip the first page (usually contains metadata)

    Returns:
        str: Extracted and cleaned text content
    """
    pages = soup.select(".PageText")

    if skip_first_page and pages:
        pages = pages[1:]

    body_text = ""
    for page in pages:
        page_text = extract_page_content(page)
        body_text += page_text + "\n"

    return clean_text(body_text)


def extract_content_from_file(file_path: str, skip_first_page: bool = True) -> str:
    """
    Extract content from an HTML file.

    Args:
        file_path: Path to the HTML file
        skip_first_page: Whether to skip the first page (usually contains metadata)

    Returns:
        str: Extracted and cleaned text content
    """
    with open(file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")
    return extract_content_from_soup(soup, skip_first_page)


def extract_content_from_files(file_paths: List[str]) -> str:
    """
    Extract content from multiple HTML files and combine them.

    Args:
        file_paths: List of paths to HTML files

    Returns:
        str: Combined and cleaned text content
    """
    combined_text = ""

    for i, file_path in enumerate(file_paths):
        # Skip metadata page only for the first file
        skip_first = i == 0
        content = extract_content_from_file(file_path, skip_first)
        combined_text += content + "\n\n"

    return clean_text(combined_text)
