import argparse
from pathlib import Path
import csv


def combine_csv_files(directory: Path, output_file=None):
    csv_files = list(directory.glob("*.csv"))

    if not csv_files:
        print("No CSV files found in the directory.")
        return

    combined_data = []
    consistent_headers = None

    for csv_file in csv_files:
        with csv_file.open('r', newline='') as file:
            reader = csv.reader(file)
            headers = next(reader)

            # Check if headers are consistent with previous files
            if consistent_headers is None:
                consistent_headers = headers
            elif consistent_headers != headers:
                print(f"Headers in {csv_file.name} are inconsistent with previous files.")
                return

            for row in reader:
                combined_data.append(row)

    if combined_data:
        output_file = output_file or directory / 'combined_output.csv'

        with output_file.open('w', newline='') as output_csv:
            writer = csv.writer(output_csv)
            writer.writerow(consistent_headers)  # Write the consistent headers
            writer.writerows(combined_data)

        print("CSV files successfully combined into 'combined_output.csv'")
    else:
        print("No data found in the CSV files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine CSV files in a directory.")
    parser.add_argument("directory", type=Path, help="The input directory containing CSV files.")
    parser.add_argument("--output-file", "-o", type=Path, help="Output file name (optional).")
    args = parser.parse_args()

    combine_csv_files(args.directory)


# Example usage:
# input_directory = "/path/to/your/input/directory"
# combine_csv_files(input_directory)
