#!/usr/bin/env python3
"""
Script to create an NLTK corpus from Shamela books where author death date is before 1214 Hijri.
"""

import json
import logging
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import nltk
from nltk.corpus.reader.plaintext import PlaintextCorpusReader
from nltk.probability import FreqDist
from nltk.util import ngrams

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

    def load_corpus(self) -> Optional[PlaintextCorpusReader]:
        """Load the created corpus using NLTK's PlaintextCorpusReader."""
        corpus_dir = os.path.join(self.output_dir, "shamela_corpus")

        if not os.path.exists(corpus_dir):
            logger.error(f"Corpus directory not found at {corpus_dir}")
            return None

        corpus = PlaintextCorpusReader(
            corpus_dir,
            r".*\.txt",
            encoding="utf8",
            paragraph_block_reader=self._read_paragraphs,
        )

        logger.info(f"Loaded corpus with {len(corpus.fileids())} files")
        return corpus

    @staticmethod
    def _read_paragraphs(stream):
        """Custom paragraph reader that splits text on blank lines."""
        paragraphs = []
        current = []

        for line in stream:
            line = line.strip()
            if line:
                current.append(line)
            else:
                if current:
                    paragraphs.append(" ".join(current))
                    current = []

        if current:
            paragraphs.append(" ".join(current))

        return paragraphs

    def analyze_ngrams(
        self, n: int = 5, top_k: int = 20
    ) -> List[Tuple[Tuple[str, ...], int]]:
        """
        Analyze the most frequent n-grams in the corpus.

        Args:
            n: Size of n-grams
            top_k: Number of top n-grams to return

        Returns:
            List of (n-gram, frequency) tuples
        """
        corpus = self.load_corpus()
        if not corpus:
            return []

        # Tokenize all words in the corpus
        all_words = []
        for fileid in corpus.fileids():
            words = corpus.words(fileid)
            all_words.extend(words)

        # Generate n-grams
        all_ngrams = list(ngrams(all_words, n))

        # Count frequencies
        fdist = FreqDist(all_ngrams)

        # Get top k n-grams
        top_ngrams = fdist.most_common(top_k)

        return top_ngrams

    def run(self) -> None:
        """Run the complete corpus creation and analysis process."""
        self.load_metadata()
        self.select_books()
        self.create_corpus()

        # Analyze 5-grams
        top_5grams = self.analyze_ngrams(n=5, top_k=20)

        print("\nTop 20 5-grams in the corpus:")
        print("============================")
        for i, (ngram, count) in enumerate(top_5grams, 1):
            print(f"{i}. {' '.join(ngram)} (Frequency: {count})")


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
