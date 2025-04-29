# WhatsApp Voice Note Transcriber

A simple script to transcribe WhatsApp voice notes using OpenAI's Whisper API.

## Prerequisites

- Python 3.12 or higher
- `uv` for dependency management
- `ffmpeg` for audio conversion

## Setup

1. Install ffmpeg:
   - Mac: `brew install ffmpeg`
   - Windows: Download from https://ffmpeg.org/download.html
   - Linux: `sudo apt-get install ffmpeg`

2. Create and activate environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   uv pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and add your OpenAI API key:
   ```bash
   cp .env.example .env
   ```

## Usage

1. Place your WhatsApp voice notes (`.opus` files) in the `data/raw` directory.

2. Run the script:
   ```bash
   python main.py
   ```

3. Find your transcripts in the `data/transcribed` directory.

## Directory Structure

- `data/raw`: Place your `.opus` files here
- `data/processed`: Converted `.wav` files (temporary)
- `data/transcribed`: Output transcripts

## Logging

Processing logs are saved to `processing.log` in the project root.
