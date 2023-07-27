import csv
import argparse
from pathlib import Path


def append_suffix_to_csv(input_file, output_file, column_name, suffix):
    with open(input_file, 'r', encoding='utf-8') as csv_in_file:
        with open(output_file, 'w', newline='', encoding='utf-8') as csv_out_file:
            reader = csv.DictReader(csv_in_file)
            fieldnames = reader.fieldnames
            writer = csv.DictWriter(csv_out_file, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                if column_name in row:
                    row[column_name] += suffix
                writer.writerow(row)

    print(f"File saved to: {output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CLI command to append a suffix to a column of a CSV file.")
    parser.add_argument("input_file", type=Path, help="Input CSV file path.")
    parser.add_argument("output_file", type=Path, help="Output CSV file path.")
    parser.add_argument("column_name", help="Name of the column to which the suffix will be appended.")
    parser.add_argument("suffix", help="Suffix to append to the specified column.")
    args = parser.parse_args()

    append_suffix_to_csv(args.input_file, args.output_file, args.column_name, args.suffix)

# Usage
# python csv_suffix_appender.py input_file.csv output_file.csv column_name suffix
