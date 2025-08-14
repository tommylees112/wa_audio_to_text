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

6. extract-audio (Extract Audio from Video)
   - Command: extract-audio <video_file> [output_dir]
   - Purpose: Extracts audio from MP4 video file to WAV format
   - Example: python cli.py extract-audio "data/raw/video.mp4" "data/processed"

7. process-video (Complete Video Processing)
   - Command: process-video <video_file>
   - Purpose: Extracts audio from video and transcribes it
   - Example: python cli.py process-video "data/raw/video.mp4"
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

from main import extract_audio_from_mp4, transcribe_audio, PROCESSED_DIR, TRANSCRIBED_DIR


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


@cli.command("transcribe")
@click.argument("input_dir")
@click.argument("output_dir")
@click.option("--model", "-m", help="Whisper model size", default="base")
@click.option("--timestamps/--no-timestamps", default=True, help="Include timestamps in output")
def transcribe(input_dir: str, output_dir: str, model: str = "base", timestamps: bool = True) -> None:
    """Transcribe all .wav audio files in a directory using Whisper.

    Args:
        input_dir: Directory containing .wav files (e.g., "data/processed")
        output_dir: Directory to save transcript files (e.g., "data/transcribed")
        model: Whisper model size (tiny, base, small, medium, large)
        timestamps: Include timestamps in the transcription output

    Example:
        $ python cli.py transcribe "data/processed" "data/transcribed"
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    wav_files = list(input_path.glob("*.wav"))
    if not wav_files:
        logger.warning(f"No .wav files found in {input_dir}")
        click.echo(f"No .wav files found in {input_dir}")
        return

    processed = 0
    skipped = 0
    failed = 0

    for wav_file in wav_files:
        transcript_file = output_path / f"{wav_file.stem}.txt"
        if transcript_file.exists():
            logger.info(f"Transcript already exists for {wav_file.name}, skipping.")
            skipped += 1
            continue
        
        try:
            transcript = transcribe_audio(wav_file, model_str=model, timestamps=timestamps)
            transcript_file.write_text(transcript)
            logger.success(f"Transcribed {wav_file.name}")
            processed += 1
        except Exception as e:
            logger.error(f"Error transcribing {wav_file.name}: {str(e)}")
            failed += 1
            continue

    click.echo(
        f"Transcription complete. Processed: {processed}, Skipped: {skipped}, Failed: {failed}"
    )


@cli.command("extract-audio")
@click.argument("video_file")
@click.option("--output-dir", "-o", help="Output directory for WAV file", default="data/processed")
def extract_audio(video_file: str, output_dir: str = "data/processed") -> None:
    """Extract audio from an MP4 video file to WAV format.

    Args:
        video_file: Path to the MP4 video file
        output_dir: Directory to save the WAV file (default: data/processed)

    Example:
        $ python cli.py extract-audio "data/raw/video.mp4"
        $ python cli.py extract-audio "data/raw/video.mp4" -o "custom/output"
    """
    video_path = Path(video_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        click.echo(f"Error: Video file not found: {video_path}")
        return

    if not video_path.suffix.lower() == ".mp4":
        logger.error(f"Only MP4 files are supported, got: {video_path.suffix}")
        click.echo(f"Error: Only MP4 files are supported, got: {video_path.suffix}")
        return

    try:
        wav_file = extract_audio_from_mp4(video_path, output_path)
        click.echo(f"Successfully extracted audio to: {wav_file}")
    except Exception as e:
        logger.error(f"Failed to extract audio: {str(e)}")
        click.echo(f"Error: Failed to extract audio: {str(e)}")


@cli.command("process-video")
@click.argument("video_file")
@click.option("--model", "-m", help="Whisper model size", default="base")
@click.option("--timestamps/--no-timestamps", default=True, help="Include timestamps in output")
def process_video(video_file: str, model: str = "base", timestamps: bool = True) -> None:
    """Complete video processing: extract audio and transcribe it.

    Args:
        video_file: Path to the MP4 video file
        model: Whisper model size (tiny, base, small, medium, large)
        timestamps: Include timestamps in the transcription output

    Example:
        $ python cli.py process-video "data/raw/video.mp4"
        $ python cli.py process-video "data/raw/video.mp4" -m small --no-timestamps
    """
    video_path = Path(video_file)
    
    if not video_path.exists():
        logger.error(f"Video file not found: {video_path}")
        click.echo(f"Error: Video file not found: {video_path}")
        return

    if not video_path.suffix.lower() == ".mp4":
        logger.error(f"Only MP4 files are supported, got: {video_path.suffix}")
        click.echo(f"Error: Only MP4 files are supported, got: {video_path.suffix}")
        return

    try:
        # Step 1: Extract audio
        click.echo("Step 1: Extracting audio from video...")
        wav_file = extract_audio_from_mp4(video_path, PROCESSED_DIR)
        click.echo(f"✓ Audio extracted to: {wav_file}")

        # Step 2: Transcribe audio
        click.echo("Step 2: Transcribing audio...")
        transcribe_audio(wav_file, model_str=model, timestamps=timestamps)
        
        # The transcript is automatically saved by transcribe_audio function
        transcript_file = TRANSCRIBED_DIR / f"{wav_file.stem}.txt"
        click.echo(f"✓ Transcript saved to: {transcript_file}")
        
        click.echo("🎉 Video processing completed successfully!")

    except Exception as e:
        logger.error(f"Failed to process video: {str(e)}")
        click.echo(f"Error: Failed to process video: {str(e)}")


if __name__ == "__main__":
    cli()
