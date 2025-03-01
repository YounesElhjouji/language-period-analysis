import os
import argparse
from pathlib import Path


def convert_bok_to_txt(input_file: str, output_file: str = None) -> None:
    """
    Convert a .bok file to .txt format with special handling for undefined characters

    Args:
        input_file (str): Path to the input .bok file
        output_file (str, optional): Path to the output .txt file. If None,
                                   uses the same name as input with .txt extension
    """
    try:
        # If no output file specified, create one based on input filename
        if output_file is None:
            output_file = str(Path(input_file).with_suffix(".txt"))

        # First read the raw bytes
        with open(input_file, "rb") as raw_file:
            raw_content = raw_file.read()

        # Try decoding with 'cp1256' (Arabic Windows encoding)
        content = raw_content.decode("cp1256", errors="replace")

        # Write the content to txt file in UTF-8
        with open(output_file, "w", encoding="utf-8") as txt_file:
            txt_file.write(content)

        print(f"Successfully converted {input_file} to {output_file}")

    except Exception as e:
        print(f"Error converting file: {str(e)}")

        # Try alternative approach if first method fails
        try:
            with open(input_file, "rb") as raw_file:
                content = raw_file.read().decode("iso-8859-6", errors="replace")

            with open(output_file, "w", encoding="utf-8") as txt_file:
                txt_file.write(content)

            print("Successfully converted using fallback encoding")

        except Exception as e:
            print(f"Fallback conversion also failed: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Convert .bok files to .txt format")
    parser.add_argument("input", help="Input .bok file or directory")
    parser.add_argument("-o", "--output", help="Output .txt file (optional)")
    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Process directories recursively"
    )

    args = parser.parse_args()

    # Handle single file conversion
    if os.path.isfile(args.input):
        if not args.input.endswith(".bok"):
            print("Error: Input file must have .bok extension")
            return
        convert_bok_to_txt(args.input, args.output)

    # Handle directory conversion
    elif os.path.isdir(args.input):
        if args.output:
            print("Warning: Output argument is ignored when processing directories")

        for root, _, files in os.walk(args.input):
            for file in files:
                if file.endswith(".bok"):
                    input_path = os.path.join(root, file)
                    convert_bok_to_txt(input_path)

            if not args.recursive:
                break

    else:
        print("Error: Input path does not exist")


if __name__ == "__main__":
    main()
