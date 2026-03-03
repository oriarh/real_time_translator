import os
import subprocess
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(BASE_DIR, "videos")
os.makedirs(MEDIA_DIR, exist_ok=True)


@app.route("/media/<path:filename>", methods=["GET"])
def serve_media(filename):
    return send_from_directory(MEDIA_DIR, filename, as_attachment=False)


@app.route("/translate", methods=["POST"])
def run_script():
    data = request.get_json() or {}
    video_id = data.get("video_id")
    target_language = data.get("target_language")

    if not video_id or not target_language:
        return (
            jsonify({"error": "Missing parameters 'video_id' and 'target_language'"}),
            400,
        )

    try:
        result = subprocess.run(
            ["python3", "generate-local.py", str(video_id), str(target_language)],
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

        return jsonify({"output": output_url, "local_file": output_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
