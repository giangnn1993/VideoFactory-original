import argparse
from pathlib import Path
import csv


def combine_csv_files(directory: Path):
    csv_files = list(directory.glob("*.csv"))

    if not csv_files:
        print("No CSV files found in the directory.")
        return

    combined_data = []
    unique_headers = set()

    for csv_file in csv_files:
        with csv_file.open('r', newline='') as file:
            reader = csv.reader(file)
            headers = next(reader)

            for header in headers:
                unique_headers.add(header)

            for row in reader:
                combined_data.append(row)

    if combined_data:
        output_file = directory / 'combined_output.csv'

        with output_file.open('w', newline='') as output_csv:
            writer = csv.writer(output_csv)
            writer.writerow(list(unique_headers))
            writer.writerows(combined_data)

        print("CSV files successfully combined into 'combined_output.csv'")
    else:
        print("No data found in the CSV files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine CSV files in a directory.")
    parser.add_argument("directory", type=Path, help="The input directory containing CSV files.")
    args = parser.parse_args()

    combine_csv_files(args.directory)


# Example usage:
# input_directory = "/path/to/your/input/directory"
# combine_csv_files(input_directory)
