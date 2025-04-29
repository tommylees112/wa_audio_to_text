import glob
import os
import re
import shutil
from typing import List

import click


@click.group()
def cli() -> None:
    """A CLI tool for processing transcribed files.

    This tool provides commands for managing and processing transcribed audio files,
    including moving files, concatenating multiple transcripts, and cleaning up timestamps.
    """
    pass


@cli.command()
@click.argument("source_pattern")
@click.argument("target_dir")
def mv(source_pattern: str, target_dir: str) -> None:
    """Move files matching a glob pattern to a target directory.

    Args:
        source_pattern: A glob pattern specifying which files to move (e.g., "data/transcribed/*.txt")
        target_dir: The destination directory where files will be moved (e.g., "data/transcribed/nina")

    Examples:
        Move all .txt files from transcribed directory to a subdirectory:
        $ python cli.py mv "data/transcribed/*.txt" "data/transcribed/nina"
    """
    # Create target directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)

    # Get all files matching the pattern
    files: List[str] = glob.glob(source_pattern)

    for file_path in files:
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            target_path = os.path.join(target_dir, filename)
            shutil.move(file_path, target_path)
            click.echo(f"Moved {filename} to {target_dir}")


@cli.command()
@click.argument("source_dir")
@click.option("--output", "-o", help="Output file path")
def concatenate_files(source_dir: str, output: str | None) -> None:
    """Concatenate all .txt files in a directory into a single file.

    Args:
        source_dir: Directory containing .txt files to concatenate (e.g., "data/transcribed/nina")
        output: Optional path for the output file. If not provided, uses directory name + .txt

    Examples:
        Concatenate all files in the nina directory:
        $ python cli.py concatenate-files "data/transcribed/nina"

        Specify custom output file:
        $ python cli.py concatenate-files "data/transcribed/nina" -o "combined_transcripts.txt"
    """
    if not output:
        # Use directory name as default output filename
        dir_name = os.path.basename(os.path.normpath(source_dir))
        output = os.path.join(os.path.dirname(source_dir), f"{dir_name}.txt")

    # Get all .txt files in the directory
    files: List[str] = glob.glob(os.path.join(source_dir, "*.txt"))
    files.sort()  # Sort files for consistent ordering

    with open(output, "w") as outfile:
        for file_path in files:
            with open(file_path, "r") as infile:
                outfile.write(infile.read())
                outfile.write("\n")  # Add newline between files

    click.echo(f"Concatenated files to {output}")


@cli.command()
@click.argument("input_file")
@click.option("--output", "-o", help="Output file path")
def remove_timestamps(input_file: str, output: str | None) -> None:
    """Remove timestamps from a transcribed text file.

    Args:
        input_file: Path to the input file containing timestamps (e.g., "data/transcribed/PTT-20250428-WA0012.txt")
        output: Optional path for the output file. If not provided, adds 'clean_' prefix to input filename

    Examples:
        Remove timestamps from a file:
        $ python cli.py remove-timestamps "data/transcribed/PTT-20250428-WA0012.txt"

        Specify custom output file:
        $ python cli.py remove-timestamps "data/transcribed/PTT-20250428-WA0012.txt" -o "clean_transcript.txt"
    """
    if not output:
        # Create output filename by adding 'clean_' prefix
        dir_name = os.path.dirname(input_file)
        base_name = os.path.basename(input_file)
        output = os.path.join(dir_name, f"clean_{base_name}")

    # Pattern to match timestamps like [00:00:00.000 -> 00:00:08.160]
    timestamp_pattern = r"\[\d{2}:\d{2}:\d{2}\.\d{3} -> \d{2}:\d{2}:\d{2}\.\d{3}\]"

    with open(input_file, "r") as infile, open(output, "w") as outfile:
        for line in infile:
            # Remove timestamp and clean up the line
            clean_line = re.sub(timestamp_pattern, "", line).strip()
            if clean_line:  # Only write non-empty lines
                outfile.write(clean_line + "\n")

    click.echo(f"Removed timestamps from {input_file} to {output}")


if __name__ == "__main__":
    cli()
