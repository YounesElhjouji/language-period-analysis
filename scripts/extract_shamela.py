#!/usr/bin/env python3
"""
Script to extract metadata and content from Shamela HTML files.
Extracts metadata as JSON and saves the body text separately.
"""

import os
import json
import re
from bs4 import BeautifulSoup
import argparse
from pathlib import Path


def extract_shamela_metadata(soup):
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
            next_text = span.next_sibling
            if next_text:
                metadata["book_name"] = next_text.strip()

        elif "المؤلف" in field:
            next_text = span.next_sibling
            if next_text:
                author_text = next_text.strip()
                # Clean up author text
                metadata["author"] = re.sub(r"\([^)]*\)", "", author_text).strip()

                # Extract death year
                death_year_match = re.search(r"\(ت (\d+)هـ\)", author_text)
                if death_year_match:
                    metadata["author_death_year"] = death_year_match.group(1)

        elif "تحقيق" in field:
            next_text = span.next_sibling
            if next_text:
                metadata["editor"] = next_text.strip()

        elif "الناشر" in field:
            next_text = span.next_sibling
            if next_text:
                metadata["publisher"] = next_text.strip()

        elif "الطبعة" in field:
            next_text = span.next_sibling
            if next_text:
                metadata["edition"] = next_text.strip()

        elif "عدد الصفحات" in field:
            next_text = span.next_sibling
            if next_text:
                pages_text = next_text.strip()
                # Extract just the number
                num_match = re.search(r"(\d+)", pages_text)
                if num_match:
                    metadata["pages"] = num_match.group(1)
                else:
                    metadata["pages"] = pages_text

        elif "تاريخ النشر" in field:
            next_text = span.next_sibling
            if next_text:
                metadata["publication_date"] = next_text.strip()

        elif "القسم" in field:
            next_text = span.next_sibling
            if next_text:
                metadata["section"] = next_text.strip()

    # If book_name is still empty, get it from the first title span
    if not metadata["book_name"]:
        first_title = first_page.select_one(".title")
        if first_title:
            metadata["book_name"] = first_title.get_text().strip()

    return metadata


def extract_shamela_content(html_path):
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
            if (
                hasattr(element, "name")
                and element.name == "div"
                and "PageHead" in element.get("class", [])
            ):
                continue

            # Check if element is a section title
            if (
                hasattr(element, "name")
                and element.name == "span"
                and "title" in element.get("class", [])
            ):
                title_text = element.get_text().strip()
                if title_text:
                    page_text += f"\n## {title_text}\n"
                continue

            # Handle paragraph elements
            if hasattr(element, "name") and element.name == "p":
                p_text = element.get_text().strip()
                if p_text:
                    page_text += p_text + "\n"
                continue

            # Handle direct text nodes
            if isinstance(element, str) and element.strip():
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


def main():
    parser = argparse.ArgumentParser(
        description="Extract metadata and content from Shamela HTML files"
    )
    parser.add_argument("input_file", help="Path to Shamela HTML file")
    parser.add_argument(
        "-o", "--output_dir", help="Output directory (default: same as input)"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Process all .htm files in directory recursively",
    )

    args = parser.parse_args()

    # Set output directory
    if args.output_dir:
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.path.dirname(args.input_file)

    # Process single file
    if not args.recursive:
        # Get base filename without extension
        base_name = Path(args.input_file).stem

        # Extract metadata and content
        metadata, body_text = extract_shamela_content(args.input_file)

        if not metadata and not body_text:
            print(f"Error: Could not extract content from {args.input_file}")
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

    # Process all files in directory
    else:
        input_dir = args.input_file
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
            # Get relative path for output
            rel_path = os.path.relpath(htm_file, input_dir)
            base_name = Path(htm_file).stem

            # Create output subdirectories if needed
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


if __name__ == "__main__":
    main()

