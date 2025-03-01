import chardet


def detect_encoding(file_path):
    """
    Detects file encoding using chardet.
    """
    with open(file_path, "rb") as f:
        raw_data = f.read(10000)  # Read a portion of the file
    result = chardet.detect(raw_data)
    return result["encoding"]


def read_bok_file(file_path):
    """
    Reads a .bok file and extracts words/phrases, handling Arabic text.
    """
    encoding = detect_encoding(file_path)  # Detect encoding
    words = []
    try:
        with open(file_path, "r", encoding=encoding) as file:
            for line in file:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#"):  # Skip comments
                    words.append(clean_line)
    except Exception as e:
        print(f"Error reading file: {e}")
    return words


def save_as_nltk_corpus(words, output_file):
    """
    Saves extracted words/phrases in a simple NLTK-friendly text format.
    """
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(words))
        print(f"NLTK corpus saved to {output_file}")
    except Exception as e:
        print(f"Error saving file: {e}")


def main():
    input_file = "../data/4479.bok"  # Change this to your .bok file
    output_file = "../data/4479.txt"  # Output file for NLTK usage

    encoding = detect_encoding(input_file)
    print(f"Detected encoding: {encoding}")

    words = read_bok_file(input_file)

    if words:
        save_as_nltk_corpus(words, output_file)
        print(
            "Conversion successful. Use `nltk.corpus.PlaintextCorpusReader` to read it in NLTK."
        )
    else:
        print("No valid words extracted.")


if __name__ == "__main__":
    main()
