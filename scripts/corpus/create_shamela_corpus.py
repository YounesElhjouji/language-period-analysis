#!/usr/bin/env python3
"""
Script to create an NLTK corpus from Shamela books where author death date is before 1214 Hijri.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict

import nltk
from nltk.corpus.reader.plaintext import PlaintextCorpusReader

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ShamelaCorpus:
    """Class to create and analyze a corpus from Shamela books."""

    def __init__(self, processed_dir: str, output_dir: str, max_death_year: int = 1214):
        """
        Initialize the ShamelaCorpus.

        Args:
            processed_dir: Directory containing processed Shamela books
            output_dir: Directory to save the corpus
            max_death_year: Maximum author death year to include in corpus
        """
        self.processed_dir = processed_dir
        self.output_dir = output_dir
        self.max_death_year = max_death_year
        self.metadata = {}
        self.selected_books = []

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Ensure NLTK data is available
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            logger.info("Downloading NLTK punkt tokenizer...")
            nltk.download("punkt")

    def load_metadata(self) -> None:
        """Load metadata from the processed directory."""
        metadata_path = os.path.join(self.processed_dir, "metadata.json")

        if not os.path.exists(metadata_path):
            raise FileNotFoundError(f"Metadata file not found at {metadata_path}")

        with open(metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        logger.info(f"Loaded metadata for {len(self.metadata)} books")

    def select_books(self) -> None:
        """Select books based on author death year criteria."""
        self.selected_books = []

        for book_id, book_meta in self.metadata.items():
            death_year = book_meta.get("author_death_year")

            if death_year is not None:
                try:
                    death_year_int = int(death_year)
                    if death_year_int < self.max_death_year:
                        book_path = os.path.join(self.processed_dir, f"{book_id}.txt")
                        if os.path.exists(book_path):
                            self.selected_books.append((book_id, book_meta))
                except ValueError:
                    logger.warning(
                        f"Invalid death year format for book {book_id}: {death_year}"
                    )

        logger.info(
            f"Selected {len(self.selected_books)} books with author death year < {self.max_death_year}"
        )

    def create_corpus(self) -> None:
        """Create the corpus by copying selected books to the output directory."""
        # Create corpus directory structure
        corpus_dir = os.path.join(self.output_dir, "shamela_corpus")
        os.makedirs(corpus_dir, exist_ok=True)

        # Create README file
        readme_path = os.path.join(corpus_dir, "README")
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("Shamela Corpus\n")
            f.write("==============\n\n")
            f.write(
                f"This corpus contains Arabic texts from Shamela books where the author's death year is before {self.max_death_year} Hijri.\n\n"
            )
            f.write("Book List:\n")

            for book_id, book_meta in self.selected_books:
                author = book_meta.get("author", "Unknown")
                death_year = book_meta.get("author_death_year", "Unknown")
                f.write(
                    f"- {book_meta.get('book_name', 'Unknown')} by {author} (d. {death_year})\n"
                )

        # Copy selected books to corpus directory
        for book_id, book_meta in self.selected_books:
            source_path = os.path.join(self.processed_dir, f"{book_id}.txt")

            # Create a sanitized filename from the book name
            book_name = book_meta.get("book_name", book_id)
            safe_name = re.sub(r"[^\w\s-]", "", book_name).strip().replace(" ", "_")
            target_path = os.path.join(corpus_dir, f"{safe_name}_{book_id}.txt")

            with (
                open(source_path, "r", encoding="utf-8") as src,
                open(target_path, "w", encoding="utf-8") as dst,
            ):
                content = src.read()
                dst.write(content)

        # Create corpus metadata
        corpus_meta = {
            "name": "Shamela Classical Arabic Corpus",
            "description": f"Arabic texts from Shamela books with author death year before {self.max_death_year} Hijri",
            "books": len(self.selected_books),
            "book_list": [
                {
                    "id": book_id,
                    "title": book_meta.get("book_name", "Unknown"),
                    "author": book_meta.get("author", "Unknown"),
                    "death_year": book_meta.get("author_death_year", "Unknown"),
                    "section": book_meta.get("section", "Unknown"),
                    "length": book_meta.get("content_length", 0),
                }
                for book_id, book_meta in self.selected_books
            ],
        }

        with open(
            os.path.join(corpus_dir, "corpus_metadata.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(corpus_meta, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Created corpus with {len(self.selected_books)} books in {corpus_dir}"
        )

    def analyze_corpus(self) -> Dict[str, Any]:
        """
        Analyze the corpus and return statistics.

        Returns:
            Dict containing corpus statistics
        """
        corpus_dir = os.path.join(self.output_dir, "shamela_corpus")

        if not os.path.exists(corpus_dir):
            logger.error(f"Corpus directory not found at {corpus_dir}")
            return {}

        start_time = time.time()

        # Load the corpus
        corpus = PlaintextCorpusReader(corpus_dir, r".*\.txt", encoding="utf8")

        load_time = time.time() - start_time
        logger.info(f"Loaded corpus in {load_time:.2f} seconds")

        # Count words and characters
        total_words = 0
        total_chars = 0
        word_count_by_file = {}

        for fileid in corpus.fileids():
            # Count words in this file
            words = re.findall(r"\b\w+\b", corpus.raw(fileid))
            word_count = len(words)
            total_words += word_count
            total_chars += len(corpus.raw(fileid))

            # Store word count for this file
            word_count_by_file[fileid] = word_count

        # Calculate average words per book
        avg_words_per_book = (
            total_words / len(corpus.fileids()) if corpus.fileids() else 0
        )

        # Get largest and smallest books
        if word_count_by_file:
            largest_book = max(word_count_by_file.items(), key=lambda x: x[1])
            smallest_book = min(word_count_by_file.items(), key=lambda x: x[1])
        else:
            largest_book = ("none", 0)
            smallest_book = ("none", 0)

        # Compile statistics
        stats = {
            "num_books": len(corpus.fileids()),
            "total_words": total_words,
            "total_chars": total_chars,
            "avg_words_per_book": avg_words_per_book,
            "largest_book": {
                "filename": largest_book[0],
                "word_count": largest_book[1],
            },
            "smallest_book": {
                "filename": smallest_book[0],
                "word_count": smallest_book[1],
            },
            "load_time_seconds": load_time,
        }

        return stats

    def run(self) -> None:
        """Run the complete corpus creation and analysis process."""
        self.load_metadata()
        self.select_books()
        self.create_corpus()

        # Analyze corpus
        stats = self.analyze_corpus()

        # Print corpus statistics
        print("\nShamela Corpus Statistics:")
        print("=========================")
        print(f"Number of books: {stats['num_books']}")
        print(f"Total words: {stats['total_words']:,}")
        print(f"Total characters: {stats['total_chars']:,}")
        print(f"Average words per book: {stats['avg_words_per_book']:.2f}")
        print(
            f"Largest book: {stats['largest_book']['filename']} ({stats['largest_book']['word_count']:,} words)"
        )
        print(
            f"Smallest book: {stats['smallest_book']['filename']} ({stats['smallest_book']['word_count']:,} words)"
        )
        print(f"Corpus load time: {stats['load_time_seconds']:.2f} seconds")

        # Save statistics to file
        stats_path = os.path.join(
            self.output_dir, "shamela_corpus", "corpus_stats.json"
        )
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved corpus statistics to {stats_path}")


def main():
    """Main function to create and analyze the Shamela corpus."""
    # Define directories
    processed_dir = "data/shamelaProcessed"
    output_dir = "data/corpus"

    # Create and analyze corpus
    corpus_builder = ShamelaCorpus(processed_dir, output_dir)
    corpus_builder.run()


if __name__ == "__main__":
    main()
