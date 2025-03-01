# Language Period Analysis Code Guidelines

## Build & Run Commands
- Create virtual environment: `python -m venv venv`
- Activate virtual environment: `source venv/bin/activate` (macOS/Linux)
- Install dependencies: `pip install -r requirements.txt`
- Convert BOK files: `python scripts/bokToTxt.py <input_file> <output_file>`
- Optional args for conversion: `-r/--recursive` for directory processing

## Code Style Guidelines
- **Imports**: Standard library first, then third-party, then local modules, each group separated by a blank line
- **Formatting**: 4-space indentation, max line length 88 characters
- **Type Annotations**: Use type hints for function parameters and return values
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Use try/except with specific exceptions, provide useful error messages
- **Documentation**: Docstrings for all modules, classes, and functions using Google style
- **Module Structure**: Private functions prefixed with underscore, main executable code in `if __name__ == "__main__"` block

## Text Processing Conventions
- Use chardet for automatic encoding detection when processing Arabic text files
- Handle and preserve Arabic language text encoding properly
- When working with corpus data, provide clear metadata regarding sources and time periods