import os
import subprocess
import sys
import glob
import shutil
import json
from yt_dlp import YoutubeDL
from gtts import gTTS
from deep_translator import GoogleTranslator
import openai
from dotenv import load_dotenv

# Set your OpenAI API key (or replace with another ASR API if needed)

load_dotenv()

whisper_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Ensure ffmpeg is installed and available in PATH.
FFMPEG_PATH = "ffmpeg"


# Helper function to run shell commands
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Error executing command: {command}\n{result.stderr}")


def validate_video_file(video_path):
    if not os.path.isfile(video_path):
        return False
    if os.path.getsize(video_path) == 0:
        return False
    if shutil.which("ffprobe") is None:
        return True

    ffprobe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(ffprobe_cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False

    stream_types = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return "video" in stream_types and "audio" in stream_types


# Step 1: Download the YouTube video locally using yt-dlp
def download_youtube_video(video_id, save_path):

    video_url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = os.path.join(save_path, f"{video_id}.%(ext)s")
    ydl_opts = {
        # Prefer MP4-compatible streams, but gracefully fall back when unavailable.
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)

    requested = info.get("requested_downloads") or []
    for item in requested:
        filepath = item.get("filepath")
        if filepath and os.path.exists(filepath):
            return filepath

    for candidate in glob.glob(os.path.join(save_path, f"{video_id}.*")):
        if os.path.isfile(candidate) and not candidate.endswith(".part"):
            return candidate

    raise FileNotFoundError("yt-dlp completed but no output video file was found.")


# Step 2: Extract audio using ffmpeg
def extract_audio(video_path):
    base, _ = os.path.splitext(video_path)
    audio_path = f"{base}.mp3"
    command = f"{FFMPEG_PATH} -i {video_path} -q:a 0 -map a {audio_path}"
    print("==command==", command)
    run_command(command)
    print(f"Extracted audio to {audio_path}")
    return audio_path


# Step 3: Convert audio to text (using OpenAI Whisper API or another ASR service)
def audio_to_text(audio_path):
    with open(audio_path, "rb") as audio_file:
        response = whisper_client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
        transcription = response.text
        print(f"Transcribed text: {transcription}")
        return transcription


# Step 4: Translate text to target language using Google Translate
def translate_text(text, target_language):
    translated = GoogleTranslator(source="auto", target=target_language).translate(text)
    print(f"Translated text: {translated}")
    return translated


# Step 5: Generate an audio file from translated text using gTTS
def text_to_speech(text, target_language, output_audio):
    tts = gTTS(text=text, lang=target_language)
    tts.save(output_audio)
    print(f"Generated translated audio at {output_audio}")


# Step 6: Create a new video with original video and generated audio
def create_new_video(original_video, generated_audio, output_video):
    run_command(
        f"{FFMPEG_PATH} -i {original_video} -i {generated_audio} -c:v copy -map 0:v:0 -map 1:a:0 -shortest {output_video}"
    )
    print(f"Created new video at {output_video}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print("Usage: python script.py <youtube_video_id> <target_language> [force_regenerate]")
        sys.exit(1)

    if shutil.which(FFMPEG_PATH) is None:
        print(
            "An error occurred: ffmpeg is not installed or not in PATH. Install it and retry.",
            file=sys.stderr,
        )
        sys.exit(1)

    video_id = sys.argv[1]
    target_language = sys.argv[2]
    force_regenerate = False
    if len(sys.argv) == 4:
        force_regenerate = sys.argv[3].strip().lower() in {"1", "true", "yes"}

    save_path = os.path.join(os.getcwd(), "videos")
    os.makedirs(save_path, exist_ok=True)

    try:
        output_video_path = os.path.join(save_path, f"{video_id}_{target_language}.mp4")
        transcript_file_path = os.path.join(
            save_path, f"{video_id}_{target_language}.transcript.json"
        )

        if not force_regenerate and validate_video_file(output_video_path):
            print("CACHE_HIT=1")
            print(f"OUTPUT_FILE={output_video_path}")
            if os.path.isfile(transcript_file_path):
                print(f"TRANSCRIPT_FILE={transcript_file_path}")
            sys.exit(0)
        if os.path.exists(output_video_path):
            os.remove(output_video_path)
        if os.path.exists(transcript_file_path):
            os.remove(transcript_file_path)

        # Step 1: Download the YouTube video
        print("Step 1")
        video_path = download_youtube_video(video_id, save_path)
        print(f"video saved: {video_path}")

        # Step 2: Extract audio from the video
        print("Step 2")
        audio_path = extract_audio(video_path)

        # Step 3: Convert audio to text
        print("Step 3")
        transcribed_text = audio_to_text(audio_path)

        # Step 4: Translate text to the target language
        print("Step 4")
        translated_text = translate_text(transcribed_text, target_language)

        # Step 5: Generate translated audio
        print("Step 5")
        video_base, _ = os.path.splitext(video_path)
        translated_audio_path = f"{video_base}_translated.mp3"
        if os.path.exists(translated_audio_path):
            os.remove(translated_audio_path)
        text_to_speech(translated_text, target_language, translated_audio_path)

        # Step 6: Create a new video
        print("Step 6")
        output_video_path = f"{video_base}_{target_language}.mp4"
        create_new_video(video_path, translated_audio_path, output_video_path)
        if not validate_video_file(output_video_path):
            raise Exception("Generated output file failed validation")

        transcript_file_path = f"{video_base}_{target_language}.transcript.json"
        with open(transcript_file_path, "w", encoding="utf-8") as transcript_file:
            json.dump(
                {
                    "original_transcript": transcribed_text,
                    "translated_transcript": translated_text,
                },
                transcript_file,
                ensure_ascii=False,
                indent=2,
            )

        print("Process completed successfully!")
        print("CACHE_HIT=0")
        print(f"OUTPUT_FILE={output_video_path}")
        print(f"TRANSCRIPT_FILE={transcript_file_path}")
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
