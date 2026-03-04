import os
import subprocess
import time
import json
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "videos")
os.makedirs(MEDIA_DIR, exist_ok=True)
VIDEO_CACHE_TTL_HOURS = int(os.getenv("VIDEO_CACHE_TTL_HOURS", "24"))
VIDEO_CACHE_MAX_FILES = int(os.getenv("VIDEO_CACHE_MAX_FILES", "200"))
VIDEO_CLEANUP_GRACE_SECONDS = 300
MEDIA_EXTENSIONS = {".mp4", ".mp3", ".aac", ".m4a", ".webm"}


def cleanup_videos_dir():
    now = time.time()
    ttl_seconds = VIDEO_CACHE_TTL_HOURS * 3600
    candidates = []

    for filename in os.listdir(MEDIA_DIR):
        path = os.path.join(MEDIA_DIR, filename)
        if not os.path.isfile(path):
            continue
        _, ext = os.path.splitext(filename)
        if ext.lower() not in MEDIA_EXTENSIONS:
            continue
        mtime = os.path.getmtime(path)
        age_seconds = now - mtime
        if age_seconds < VIDEO_CLEANUP_GRACE_SECONDS:
            continue
        candidates.append((path, mtime, age_seconds))

    removed = 0
    for path, _, age_seconds in candidates:
        if age_seconds > ttl_seconds:
            try:
                os.remove(path)
                removed += 1
            except OSError:
                pass

    remaining = []
    for filename in os.listdir(MEDIA_DIR):
        path = os.path.join(MEDIA_DIR, filename)
        if not os.path.isfile(path):
            continue
        _, ext = os.path.splitext(filename)
        if ext.lower() not in MEDIA_EXTENSIONS:
            continue
        remaining.append((path, os.path.getmtime(path)))

    remaining.sort(key=lambda item: item[1], reverse=True)
    for path, _ in remaining[VIDEO_CACHE_MAX_FILES:]:
        try:
            os.remove(path)
            removed += 1
        except OSError:
            pass

    if removed:
        print(f"Cleanup removed {removed} old media files.")


@app.route("/media/<path:filename>", methods=["GET"])
def serve_media(filename):
    return send_from_directory(MEDIA_DIR, filename, as_attachment=False)


@app.route("/translate", methods=["POST"])
def run_script():
    data = request.get_json() or {}
    video_id = data.get("video_id")
    target_language = data.get("target_language")
    force_regenerate = bool(data.get("force_regenerate", False))

    if not video_id or not target_language:
        return (
            jsonify({"error": "Missing parameters 'video_id' and 'target_language'"}),
            400,
        )

    try:
        result = subprocess.run(
            [
                "python3",
                "generate-local.py",
                str(video_id),
                str(target_language),
                "1" if force_regenerate else "0",
            ],
            capture_output=True,
            text=True,
            cwd=BASE_DIR,
        )
        print("== generator stdout ==")
        print(result.stdout)
        print("== generator stderr ==")
        print(result.stderr)

        if result.returncode != 0:
            return (
                jsonify(
                    {
                        "error": "Translation failed",
                        "details": (result.stderr or result.stdout or "").strip(),
                    }
                ),
                500,
            )

        output_lines = [line.strip() for line in result.stdout.split("\n") if line.strip()]
        if not output_lines:
            return jsonify({"error": "Generator did not return an output path"}), 500

        output_line = next((line for line in output_lines if line.startswith("OUTPUT_FILE=")), None)
        cache_line = next((line for line in output_lines if line.startswith("CACHE_HIT=")), None)
        transcript_line = next(
            (line for line in output_lines if line.startswith("TRANSCRIPT_FILE=")), None
        )
        if not output_line:
            return (
                jsonify(
                    {
                        "error": "Generator did not emit OUTPUT_FILE marker",
                        "details": result.stdout.strip(),
                    }
                ),
                500,
            )

        output_path = output_line.split("=", 1)[1].strip()
        if not os.path.isfile(output_path):
            return jsonify({"error": f"Output file not found: {output_path}"}), 500
        if os.path.getsize(output_path) == 0:
            return jsonify({"error": f"Output file is empty: {output_path}"}), 500

        output_file = os.path.basename(output_path)
        output_url = f"{request.host_url.rstrip('/')}/media/{output_file}"
        cache_hit = False
        if cache_line:
            cache_hit = cache_line.split("=", 1)[1].strip() == "1"

        original_transcript = ""
        translated_transcript = ""
        if transcript_line:
            transcript_path = transcript_line.split("=", 1)[1].strip()
            if os.path.isfile(transcript_path):
                try:
                    with open(transcript_path, "r", encoding="utf-8") as transcript_file:
                        transcript_data = json.load(transcript_file)
                        original_transcript = transcript_data.get("original_transcript", "")
                        translated_transcript = transcript_data.get(
                            "translated_transcript", ""
                        )
                except (OSError, json.JSONDecodeError):
                    pass

        cleanup_videos_dir()

        return jsonify(
            {
                "output": output_url,
                "local_file": output_path,
                "cache_hit": cache_hit,
                "regenerated": not cache_hit,
                "original_transcript": original_transcript,
                "translated_transcript": translated_transcript,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    cleanup_videos_dir()
    app.run(host="0.0.0.0", port=8000)
