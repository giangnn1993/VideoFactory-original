import csv
import argparse
from pathlib import Path


def get_thumbnail_line_content(input_dir: Path, video_file: Path):
    stem = video_file.stem
    corresponding_dir = input_dir / stem
    txt_file_path = corresponding_dir / f'thumbnail_line_{stem}.txt'

    if txt_file_path.is_file():
        with open(txt_file_path, 'r') as txt_file:
            return txt_file.read()

    return ''


def process_files(input_dir: Path):
    video_files = list(input_dir.glob('*.[Mm][Pp][4Oo]'))

    enhanced_dir = input_dir / 'enhanced'
    enhanced_video_files = list(enhanced_dir.glob('*.[Mm][Pp][4Oo]'))

    # Create a dictionary to store the mapping between stems and paths in enhanced_video_files
    enhanced_stems_map = {file.stem: file for file in enhanced_video_files}

    file_content_map = [
        {
            "thumbnail_line": get_thumbnail_line_content(input_dir, video_file),
            "path": str(enhanced_stems_map.get(video_file.stem, ""))
        }
        for video_file in video_files
    ]

    return file_content_map


def save_to_csv(file_content_map, output_csv):
    with open(output_csv, 'w', newline='', encoding='utf-8-sig') as csv_file:
        fieldnames = ["path", "thumbnail_line"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        writer.writeheader()
        for entry in file_content_map:
            writer.writerow(entry)


def main(path):
    input_directory = Path(path)
    result_map = process_files(input_directory)

    output_csv_file = input_directory / 'paths.csv'
    save_to_csv(result_map, output_csv_file)

    print(f"File saved to: {output_csv_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process video files and save data to a CSV file.")
    parser.add_argument("path", type=str, help="Path to the input directory")
    args = parser.parse_args()

    main(args.path)
