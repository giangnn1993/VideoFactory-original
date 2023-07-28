import argparse
import pandas as pd
from pathlib import Path


def generate_line_files(input_csv: Path):
    # Read the CSV file into a DataFrame
    df = pd.read_csv(input_csv)

    # Extract 'quote' and 'short' columns from the DataFrame
    quote_lines = df['quote'].tolist()
    short_lines = df['short'].tolist()

    # Get the total number of lines
    total_lines = max(len(quote_lines), len(short_lines))

    # Generate lines.txt
    lines_file_path = input_csv.parent / 'lines.txt'
    with open(lines_file_path, 'w', encoding='utf-8') as lines_file:
        for i in range(1, total_lines + 1):
            line = f"[{str(i).zfill(len(str(total_lines)))}] {quote_lines[i-1]}"
            if i != total_lines:
                line += '\n'
            lines_file.write(line)

    # Generate thumbnail_lines.txt
    thumbnail_lines_file_path = input_csv.parent / 'thumbnail_lines.txt'
    with open(thumbnail_lines_file_path, 'w', encoding='utf-8') as thumbnail_lines_file:
        for i in range(1, total_lines + 1):
            line = f"[{str(i).zfill(len(str(total_lines)))}] {short_lines[i-1]}"
            if i != total_lines:
                line += '\n'
            thumbnail_lines_file.write(line)

    print("Files 'lines.txt' and 'thumbnail_lines.txt' generated successfully.")

    return lines_file_path, thumbnail_lines_file_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 'lines.txt' and 'thumbnail_lines.txt' from a CSV file.")
    parser.add_argument("input_csv", type=Path, help="Path to the input CSV file.")
    args = parser.parse_args()

    generate_line_files(args.input_csv)


# Example usage:
# Replace 'input.csv' with the path to your CSV file
# generate_line_files(Path(r'input.csv'))
