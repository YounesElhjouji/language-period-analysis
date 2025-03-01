#!/usr/bin/env python3
"""
Script to extract metadata and content from Shamela HTML files.
Extracts metadata as JSON and saves the body text separately.
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Dict, Tuple, Optional, Union, List, Any

from bs4 import BeautifulSoup, Tag, NavigableString


def extract_shamela_metadata(soup: BeautifulSoup) -> Dict[str, str]:
    """
    Extract metadata from the first page of a Shamela HTML file

    Args:
        soup: BeautifulSoup object of the HTML file

    Returns:
        dict: Metadata dictionary
    """
    metadata = {
        "book_name": "",
        "author": "",
        "author_death_year": "",
        "section": "",
        "publisher": "",
        "edition": "",
        "pages": "",
        "publication_date": "",
        "editor": "",
    }

    # Get first page which contains metadata
    first_page = soup.select_one(".PageText")
    if not first_page:
        return metadata

    # Find all spans with class 'title' followed by text
    title_spans = first_page.find_all("span", class_="title")

    # Process each title span and its following text
    for span in title_spans:
        # Get the span text which contains the metadata field name
        field = span.get_text().strip()

        # Check each metadata field
        if "الكتاب" in field:
            # Find the text after this span
            next_element = span.next_sibling
            if next_element:
                metadata["book_name"] = get_element_text(next_element)

        elif "المؤلف" in field:
            # We need to collect all text nodes and elements after this span until the next span
            author_parts = []
            current = span.next_sibling

            # Collect all text and elements until the next span or p tag
            while current and not (
                isinstance(current, Tag) and current.name in ["span", "p"]
            ):
                if isinstance(current, NavigableString):
                    author_parts.append(current.strip())
                else:
                    author_parts.append(get_element_text(current))
                current = current.next_sibling

            # Join all parts to get the complete author text
            author_text = " ".join(filter(None, author_parts))
            print(f"Complete author text: {author_text}")

            # Extract death year - just get the first number in the text
            year_match = re.search(r"(\d+)", author_text)
            if year_match:
                metadata["author_death_year"] = year_match.group(1)
                print(f"Found number: {metadata['author_death_year']}")

            # Clean up author text - remove parenthetical content
            cleaned_author = re.sub(r"\([^)]*\)", "", author_text).strip()
            metadata["author"] = cleaned_author

        elif "تحقيق" in field:
            next_element = span.next_sibling
            if next_element:
                metadata["editor"] = get_element_text(next_element)

        elif "الناشر" in field:
            next_element = span.next_sibling
            if next_element:
                metadata["publisher"] = get_element_text(next_element)

        elif "الطبعة" in field:
            next_element = span.next_sibling
            if next_element:
                metadata["edition"] = get_element_text(next_element)

        elif "عدد الصفحات" in field:
            next_element = span.next_sibling
            if next_element:
                pages_text = get_element_text(next_element)
                # Extract just the number
                num_match = re.search(r"(\d+)", pages_text)
                if num_match:
                    metadata["pages"] = num_match.group(1)
                else:
                    metadata["pages"] = pages_text

        elif "تاريخ النشر" in field:
            next_element = span.next_sibling
            if next_element:
                metadata["publication_date"] = get_element_text(next_element)

        elif "القسم" in field:
            next_element = span.next_sibling
            if next_element:
                metadata["section"] = get_element_text(next_element)

    # If book_name is still empty, get it from the first title span
    if not metadata["book_name"]:
        first_title = first_page.select_one(".title")
        if first_title:
            metadata["book_name"] = first_title.get_text().strip()

    return metadata


def get_element_text(element: Union[Tag, NavigableString, None]) -> str:
    """
    Safely extract text from a BeautifulSoup element

    Args:
        element: BeautifulSoup element (Tag, NavigableString, or None)

    Returns:
        str: Extracted text or empty string
    """
    if element is None:
        return ""
    if isinstance(element, NavigableString):
        return element.strip()
    if isinstance(element, Tag):
        return element.get_text().strip()
    return ""


def has_class(element: Any, class_name: str) -> bool:
    """
    Check if an element has a specific class

    Args:
        element: BeautifulSoup element
        class_name: Class name to check

    Returns:
        bool: True if element has the class, False otherwise
    """
    if not isinstance(element, Tag):
        return False

    classes = element.get("class", [])
    return class_name in classes if classes else False


def extract_shamela_content(html_path: str) -> Tuple[Dict[str, str], str]:
    """
    Extract metadata and body content from Shamela HTML file

    Args:
        html_path: Path to the Shamela HTML file

    Returns:
        tuple: (metadata_dict, body_text)
    """
    # Read the HTML file
    with open(html_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Parse HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract metadata
    metadata = extract_shamela_metadata(soup)

    # Extract body text (excluding the first page with metadata)
    body_pages = soup.select(".PageText")[1:]
    body_text = ""

    for page in body_pages:
        # Extract page content
        page_text = ""

        # Process each element in the page
        for element in page.children:
            # Skip page headers
            if isinstance(element, Tag) and has_class(element, "PageHead"):
                continue

            # Check if element is a section title
            if (
                isinstance(element, Tag)
                and element.name == "span"
                and has_class(element, "title")
            ):
                title_text = element.get_text().strip()
                if title_text:
                    page_text += f"\n## {title_text}\n"
                continue

            # Handle paragraph elements
            if isinstance(element, Tag) and element.name == "p":
                p_text = element.get_text().strip()
                if p_text:
                    page_text += p_text + "\n"
                continue

            # Handle direct text nodes
            if isinstance(element, NavigableString) and element.strip():
                # Clean up text
                text = element.strip()
                if text:
                    page_text += text + "\n"

        body_text += page_text + "\n"

    # Clean up body text
    body_text = re.sub(r"\n{3,}", "\n\n", body_text)  # Replace multiple newlines
    # Replace the special ellipsis character with standard one
    body_text = body_text.replace("…", "...")
    # Remove control characters
    body_text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]", "", body_text)
    body_text = body_text.strip()

    return metadata, body_text


def process_file(input_file: str, output_dir: str) -> None:
    """
    Process a single Shamela HTML file

    Args:
        input_file: Path to the input HTML file
        output_dir: Directory to save output files
    """
    # Get base filename without extension
    base_name = Path(input_file).stem

    # Extract metadata and content
    metadata, body_text = extract_shamela_content(input_file)

    if not metadata and not body_text:
        print(f"Error: Could not extract content from {input_file}")
        return

    # Save metadata as JSON
    metadata_path = os.path.join(output_dir, f"{base_name}_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # Save body text
    text_path = os.path.join(output_dir, f"{base_name}_text.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(body_text)

    print(f"Metadata saved to: {metadata_path}")
    print(f"Text content saved to: {text_path}")


def process_directory(input_dir: str, output_dir: str) -> None:
    """
    Process all HTML files in a directory recursively

    Args:
        input_dir: Input directory containing HTML files
        output_dir: Directory to save output files
    """
    if not os.path.isdir(input_dir):
        print(f"Error: {input_dir} is not a directory")
        return

    # Find all .htm files
    htm_files = []
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".htm"):
                htm_files.append(os.path.join(root, file))

    print(f"Found {len(htm_files)} .htm files to process")

    # Process each file
    for htm_file in htm_files:
        # Get relative path for output to maintain directory structure
        rel_path = os.path.relpath(htm_file, input_dir)
        base_name = Path(htm_file).stem

        # Create output subdirectories if needed to mirror input structure
        file_output_dir = os.path.join(output_dir, os.path.dirname(rel_path))
        os.makedirs(file_output_dir, exist_ok=True)

        # Extract metadata and content
        metadata, body_text = extract_shamela_content(htm_file)

        if not metadata and not body_text:
            print(f"Error: Could not extract content from {htm_file}")
            continue

        # Save metadata as JSON
        metadata_path = os.path.join(file_output_dir, f"{base_name}_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # Save body text
        text_path = os.path.join(file_output_dir, f"{base_name}_text.txt")
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(body_text)

        print(f"Processed: {htm_file}")

    print("All files processed successfully")


def main():
    parser = argparse.ArgumentParser(
        description="Extract metadata and content from Shamela HTML files"
    )
    parser.add_argument("input_file", help="Path to Shamela HTML file or directory")
    parser.add_argument(
        "-o", "--output_dir", help="Output directory for extracted data", required=True
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process all .htm files in directory recursively",
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Process single file or directory based on arguments
    if not args.recursive:
        process_file(args.input_file, output_dir)
    else:
        process_directory(args.input_file, output_dir)


if __name__ == "__main__":
    main()
