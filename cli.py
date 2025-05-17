"""
CLI Endpoints Overview:

1. mv (Move Files)
   - Command: mv <source_pattern> <target_dir>
   - Purpose: Moves files matching a glob pattern to a target directory
   - Example: python cli.py mv "data/transcribed/*.txt" "data/transcribed/nina"

2. concat (Concatenate Transcripts)
   - Command: concat <input_files> <output_file>
   - Purpose: Combines multiple transcript files into a single file
   - Example: python cli.py concat "data/transcribed/*.txt" "combined.txt"

3. clean (Clean Timestamps)
   - Command: clean <input_file> <output_file>
   - Purpose: Removes timestamps from transcript files
   - Example: python cli.py clean "input.txt" "cleaned.txt"

4. process (Process Audio Files)
   - Command: process <input_dir> <output_dir>
   - Purpose: Processes audio files in a directory
   - Example: python cli.py process "data/raw" "data/processed"

5. transcribe (Transcribe Audio Files)
   - Command: transcribe <input_dir> <output_dir>
   - Purpose: Transcribes audio files in a directory
   - Example: python cli.py transcribe "data/processed" "data/transcribed"
"""

import glob
import re
import shutil
import sys
from pathlib import Path
from typing import List, Literal

import click
from loguru import logger

sys.path.append(str(Path(__file__).parent))  # Ensure main.py can be imported


@click.group()
def cli() -> None:
    """A CLI tool for processing transcribed files.

    This tool provides commands for managing and processing transcribed audio files,
    including moving files, concatenating multiple transcripts, and cleaning up timestamps.
    """
    pass


@cli.command("mv")
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
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)

    # Get all files matching the pattern
    files: List[str] = glob.glob(source_pattern)

    for file_path in files:
        if Path(file_path).is_file():
            filename = Path(file_path).name
            target_file = target_path / filename
            shutil.move(file_path, str(target_file))
            click.echo(f"Moved {filename} to {target_dir}")


@cli.command("concat")
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
    source_path = Path(source_dir)
    if not output:
        # Use directory name as default output filename
        output = source_path.parent / f"{source_path.name}.txt"
    else:
        output = Path(output)

    # Get all .txt files in the directory
    files = list(source_path.glob("*.txt"))
    files.sort()  # Sort files for consistent ordering

    with output.open("w") as outfile:
        for file_path in files:
            with file_path.open("r") as infile:
                outfile.write(infile.read())
                outfile.write("\n")  # Add newline between files

    click.echo(f"Concatenated files to {output}")


@cli.command("clean")
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
    input_path = Path(input_file)
    logger.info(f"Starting timestamp removal from {input_path}")

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise click.FileError(str(input_path), "File not found")

    if not output:
        # Create output filename by adding 'clean_' prefix
        output = input_path.parent / f"clean_{input_path.name}"
        logger.debug(f"Using default output path: {output}")
    else:
        output = Path(output)

    # Pattern to match timestamps like [00:00:00.000 -> 00:00:08.160]
    timestamp_pattern = r"\[\d{2}:\d{2}:\d{2}\.\d{3} -> \d{2}:\d{2}:\d{2}\.\d{3}\]"

    total_lines = 0
    lines_with_timestamps = 0
    lines_removed = 0

    with input_path.open("r") as infile, output.open("w") as outfile:
        for line in infile:
            total_lines += 1
            if re.search(timestamp_pattern, line):
                lines_with_timestamps += 1
            # Remove timestamp and clean up the line
            clean_line = re.sub(timestamp_pattern, "", line).strip()
            if clean_line:  # Only write non-empty lines
                outfile.write(clean_line + "\n")
            else:
                lines_removed += 1

    logger.info(f"Processed {total_lines} lines")
    logger.info(f"Found {lines_with_timestamps} lines with timestamps")
    logger.info(f"Removed {lines_removed} empty lines")
    logger.success(f"Successfully processed {input_path} -> {output}")

    click.echo(f"Removed timestamps from {input_path} to {output}")


@cli.command("process")
@click.argument("input_dir")
@click.argument("output_dir")
@click.option("--filetype", "-f", help="File type to process", default="opus")
def process(
    input_dir: str, output_dir: str, filetype: Literal["ogg", "opus"] = "opus"
) -> None:
    """Process all .opus audio files in a directory, converting them to .wav files in the output directory.

    Args:
        input_dir: Directory containing .opus files (e.g., "data/raw")
        output_dir: Directory to save .wav files (e.g., "data/processed")

    Example:
        $ python cli.py process "data/raw" "data/processed"
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    opus_files = list(input_path.glob("*.opus"))
    if not opus_files:
        logger.warning(f"No .opus files found in {input_dir}")
        click.echo(f"No .opus files found in {input_dir}")
        return

    processed = 0
    skipped = 0
    failed = 0

    for opus_file in opus_files:
        wav_file = output_path / f"{opus_file.stem}.wav"
        if wav_file.exists():
            logger.info(f"WAV file already exists for {opus_file.name}, skipping.")
            skipped += 1
            continue
        try:
            # Use convert_opus_to_wav but override output dir
            cmd = [
                "ffmpeg",
                "-f",
                "ogg",
                "-i",
                str(opus_file),
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                str(wav_file),
            ]
            import subprocess

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(
                    f"FFmpeg conversion failed for {opus_file.name}: {result.stderr}"
                )
                failed += 1
                continue
            logger.success(f"Converted {opus_file.name} to {wav_file.name}")
            processed += 1
        except Exception as e:
            logger.error(f"Error converting {opus_file.name}: {str(e)}")
            failed += 1
            continue

    click.echo(
        f"Processing complete. Converted: {processed}, Skipped: {skipped}, Failed: {failed}"
    )


if __name__ == "__main__":
    cli()
