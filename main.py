import subprocess
from pathlib import Path
from typing import Any, Literal

import whisper
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Define paths
ROOT_DIR = Path(__file__).parent
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
TRANSCRIBED_DIR = DATA_DIR / "transcribed"


def setup_directories():
    """Create necessary directories if they don't exist."""
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"Raw data directory not found at {RAW_DIR}")

    PROCESSED_DIR.mkdir(exist_ok=True)
    TRANSCRIBED_DIR.mkdir(exist_ok=True)
    logger.info("Directories setup complete")


def convert_opus_to_wav(opus_file: Path) -> Path:
    """Convert a WhatsApp voice note to wav format using ffmpeg."""
    wav_file = PROCESSED_DIR / f"{opus_file.stem}.wav"

    if wav_file.exists():
        logger.info(f"WAV file already exists for {opus_file.name}")
        return wav_file

    try:
        # Use ffmpeg with explicit Ogg container format
        cmd = [
            "ffmpeg",
            "-f",
            "ogg",  # Explicitly specify Ogg container format
            "-i",
            str(opus_file),
            "-acodec",
            "pcm_s16le",  # Use 16-bit PCM
            "-ar",
            "16000",  # Set sample rate to 16kHz
            "-ac",
            "1",  # Convert to mono
            str(wav_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg conversion failed: {result.stderr}")

        logger.success(f"Converted {opus_file.name} to WAV")
        return wav_file
    except Exception as e:
        logger.error(f"Error converting {opus_file.name}: {str(e)}")
        raise


def extract_audio_from_mp4(mp4_file: Path, output_dir: Path = PROCESSED_DIR) -> Path:
    """Extract audio from MP4 video file to WAV format using ffmpeg."""
    wav_file = output_dir / f"{mp4_file.stem}.wav"
    
    if wav_file.exists():
        logger.info(f"WAV file already exists for {mp4_file.name}")
        return wav_file
    
    try:
        cmd = [
            "ffmpeg",
            "-i",
            str(mp4_file),
            "-vn",  # No video
            "-acodec",
            "pcm_s16le",  # Use 16-bit PCM
            "-ar",
            "16000",  # Set sample rate to 16kHz
            "-ac",
            "1",  # Convert to mono
            str(wav_file),
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"FFmpeg audio extraction failed: {result.stderr}")
        
        logger.success(f"Extracted audio from {mp4_file.name} to WAV")
        return wav_file
    except Exception as e:
        logger.error(f"Error extracting audio from {mp4_file.name}: {str(e)}")
        raise


def format_timestamp(seconds: float) -> str:
    """Format seconds into HH:MM:SS.mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"


def format_transcript(segments: list[dict], timestamps: bool = True) -> str:
    """Format the transcript with optional timestamps.

    Args:
        segments: List of transcript segments
            {"start": float, "end": float, "text": str}
        timestamps: If True, include timestamps. If False, return plain text.

    Returns:
        Formatted transcript as string
    """
    if timestamps:
        # Format with timestamps
        formatted_transcript = ""
        for segment in segments:
            start_time = format_timestamp(segment["start"])
            end_time = format_timestamp(segment["end"])
            text = segment["text"].strip()
            formatted_transcript += f"[{start_time} -> {end_time}] {text}\n"
    else:
        # Format as continuous text
        formatted_transcript = " ".join(segment["text"].strip() for segment in segments)
        # Clean up any double spaces
        formatted_transcript = " ".join(formatted_transcript.split())
        formatted_transcript += "\n"

    return formatted_transcript


def transcribe_audio(
    audio_file: Path,
    model_str: Literal["tiny", "base", "small", "medium", "large"] = "base",
    timestamps: bool = True,
    kwargs: dict[str, Any] = {},
) -> str:
    """Transcribe audio using local Whisper model with optional timestamps.

    Args:
        audio_file: Path to the audio file
        model_str: Whisper model size to use
        timestamps: Whether to include timestamps in the output
        kwargs: Additional arguments to pass to the Whisper model

    Returns:
        Formatted transcript as string
    """
    transcript_file = TRANSCRIBED_DIR / f"{audio_file.stem}.txt"

    # Check if transcript already exists
    if transcript_file.exists():
        logger.info(f"Transcript already exists for {audio_file.name}")
        return transcript_file.read_text()

    try:
        # Load the Whisper model
        model = whisper.load_model(model_str)

        # Transcribe the audio file
        result = model.transcribe(str(audio_file), **kwargs)

        # Format the transcript with or without timestamps
        formatted_transcript = format_transcript(result["segments"], timestamps)

        # Save the transcript
        transcript_file.write_text(formatted_transcript)
        logger.success(f"Saved transcript to {transcript_file}")

        return formatted_transcript
    except Exception as e:
        logger.error(f"Error transcribing {audio_file.name}: {str(e)}")
        raise


def process_files(filetype: Literal["ogg", "opus"] = "ogg"):
    """Process all opus files in the raw directory."""
    opus_files = list(RAW_DIR.glob(f"*.{filetype}"))
    if not opus_files:
        logger.warning(f"No {filetype} files found in raw directory")
        return

    for opus_file in opus_files:
        try:
            # Check if transcript already exists
            transcript_file = TRANSCRIBED_DIR / f"{opus_file.stem}.txt"
            if transcript_file.exists():
                logger.info(f"Skipping {opus_file.name} - transcript already exists")
                continue

            # Convert to WAV
            wav_file = convert_opus_to_wav(opus_file)

            # Transcribe
            logger.info(f"Transcribing {wav_file.name}")
            transcript = transcribe_audio(wav_file)

            # Save transcript
            transcript_file.write_text(transcript)
            logger.success(f"Saved transcript to {transcript_file}")

        except Exception as e:
            logger.error(f"Failed to process {opus_file.name}: {str(e)}")
            continue


def main():
    """Main execution function."""
    logger.info("Starting WhatsApp voice note transcription process")

    try:
        # Setup directories
        setup_directories()

        # Process files
        process_files()

        logger.success("Processing completed successfully")

    except Exception as e:
        logger.error(f"Process failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
