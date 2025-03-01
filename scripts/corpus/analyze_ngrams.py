#!/usr/bin/env python3
"""
Script to analyze n-grams in the Shamela corpus.
"""

import json
import logging
import os
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import nltk
from nltk.corpus.reader.plaintext import PlaintextCorpusReader
from nltk.util import ngrams

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class NGramAnalyzer:
    """Class to analyze n-grams in the Shamela corpus."""

    def __init__(self, corpus_dir: str, output_dir: str):
        """
        Initialize the NGramAnalyzer.

        Args:
            corpus_dir: Directory containing the corpus
            output_dir: Directory to save analysis results
        """
        self.corpus_dir = corpus_dir
        self.output_dir = output_dir

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

    def load_corpus(self) -> Optional[PlaintextCorpusReader]:
        """
        Load the corpus using NLTK's PlaintextCorpusReader.

        Returns:
            PlaintextCorpusReader object or None if corpus not found
        """
        if not os.path.exists(self.corpus_dir):
            logger.error(f"Corpus directory not found at {self.corpus_dir}")
            return None

        start_time = time.time()

        corpus = PlaintextCorpusReader(self.corpus_dir, r".*\.txt", encoding="utf8")

        load_time = time.time() - start_time
        logger.info(
            f"Loaded corpus with {len(corpus.fileids())} files in {load_time:.2f} seconds"
        )

        return corpus

    def analyze_ngrams(
        self, n: int, top_k: int = 100
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

        logger.info(f"Starting {n}-gram analysis...")
        start_time = time.time()

        # Process files in batches to avoid memory issues
        all_ngrams = Counter()
        batch_size = 10

        # Process files in batches
        fileids = corpus.fileids()
        for i in range(0, len(fileids), batch_size):
            batch_fileids = fileids[i : i + batch_size]
            logger.info(
                f"Processing batch {i//batch_size + 1}/{(len(fileids) + batch_size - 1)//batch_size}"
            )

            for fileid in batch_fileids:
                # Read and tokenize the file
                try:
                    raw_text = corpus.raw(fileid)
                    # Simple Arabic word tokenization (split on whitespace and punctuation)
                    words = re.findall(r"\b\w+\b", raw_text)

                    # Generate n-grams for this file
                    file_ngrams = list(ngrams(words, n))

                    # Update counter
                    all_ngrams.update(file_ngrams)
                except Exception as e:
                    logger.error(f"Error processing file {fileid}: {str(e)}")

        # Get top k n-grams
        top_ngrams = all_ngrams.most_common(top_k)

        analysis_time = time.time() - start_time
        logger.info(f"Completed {n}-gram analysis in {analysis_time:.2f} seconds")

        return top_ngrams

    def save_ngram_report(
        self, n: int, top_ngrams: List[Tuple[Tuple[str, ...], int]]
    ) -> str:
        """
        Save n-gram analysis results to a file.

        Args:
            n: Size of n-grams
            top_ngrams: List of (n-gram, frequency) tuples

        Returns:
            Path to the saved report
        """
        report_path = os.path.join(self.output_dir, f"top_{n}grams.txt")

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"Top {len(top_ngrams)} {n}-grams in the Shamela Corpus\n")
            f.write("=" * 50 + "\n\n")

            for i, (ngram, count) in enumerate(top_ngrams, 1):
                ngram_text = " ".join(ngram)
                f.write(f"{i}. {ngram_text} (Frequency: {count})\n")

        logger.info(f"Saved {n}-gram report to {report_path}")
        return report_path

    def save_ngram_json(
        self, n: int, top_ngrams: List[Tuple[Tuple[str, ...], int]]
    ) -> str:
        """
        Save n-gram analysis results to a JSON file.

        Args:
            n: Size of n-grams
            top_ngrams: List of (n-gram, frequency) tuples

        Returns:
            Path to the saved JSON file
        """
        json_path = os.path.join(self.output_dir, f"top_{n}grams.json")

        # Convert n-grams to a serializable format
        ngram_data = [
            {"ngram": " ".join(ngram), "tokens": list(ngram), "frequency": count}
            for ngram, count in top_ngrams
        ]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(ngram_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Saved {n}-gram data to {json_path}")
        return json_path

    def run_analysis(self, min_n: int = 1, max_n: int = 6, top_k: int = 100) -> None:
        """
        Run n-gram analysis for different values of n.

        Args:
            min_n: Minimum n-gram size
            max_n: Maximum n-gram size
            top_k: Number of top n-grams to return for each n
        """
        for n in range(min_n, max_n + 1):
            logger.info(f"Analyzing {n}-grams...")
            top_ngrams = self.analyze_ngrams(n, top_k)

            if top_ngrams:
                # Save results in text and JSON formats
                self.save_ngram_report(n, top_ngrams)
                self.save_ngram_json(n, top_ngrams)
            else:
                logger.warning(f"No {n}-grams found in the corpus")

        # Create a summary report
        self.create_summary_report(min_n, max_n, top_k)

    def create_summary_report(self, min_n: int, max_n: int, top_k: int) -> None:
        """
        Create a summary report of all n-gram analyses.

        Args:
            min_n: Minimum n-gram size analyzed
            max_n: Maximum n-gram size analyzed
            top_k: Number of top n-grams returned for each n
        """
        summary_path = os.path.join(self.output_dir, "ngram_analysis_summary.txt")

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("Shamela Corpus N-gram Analysis Summary\n")
            f.write("====================================\n\n")

            f.write(f"Analysis range: {min_n}-grams to {max_n}-grams\n")
            f.write(f"Top {top_k} n-grams reported for each n\n\n")

            f.write("Top 10 n-grams for each n:\n")

            for n in range(min_n, max_n + 1):
                json_path = os.path.join(self.output_dir, f"top_{n}grams.json")

                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as json_file:
                        ngram_data = json.load(json_file)

                    f.write(f"\nTop 10 {n}-grams:\n")
                    f.write("-" * 30 + "\n")

                    for i, item in enumerate(ngram_data[:10], 1):
                        f.write(
                            f"{i}. {item['ngram']} (Frequency: {item['frequency']})\n"
                        )
                else:
                    f.write(f"\nNo data available for {n}-grams\n")

        logger.info(f"Created summary report at {summary_path}")


def main():
    """Main function to analyze n-grams in the Shamela corpus."""
    # Define directories
    corpus_dir = "data/corpus/shamela_corpus"
    output_dir = "data/corpus/ngram_analysis"

    # Create analyzer and run analysis
    analyzer = NGramAnalyzer(corpus_dir, output_dir)
    analyzer.run_analysis(min_n=1, max_n=6, top_k=100)

    print("\nN-gram Analysis Complete")
    print("=======================")
    print(f"Analysis results saved to {output_dir}")
    print("Files generated:")
    for n in range(1, 7):
        print(f"- top_{n}grams.txt - Text report of top {n}-grams")
        print(f"- top_{n}grams.json - JSON data of top {n}-grams")
    print("- ngram_analysis_summary.txt - Summary of all n-gram analyses")


if __name__ == "__main__":
    main()
