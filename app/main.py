"""Flask app for the Sketch Explainer video generator."""
import os
import uuid
import threading
import traceback
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory, abort

from .script_gen import generate_script
from .tts import synthesize
from .video_render import render_video

BASE = Path(__file__).resolve().parent
OUTPUT = Path(os.environ.get("OUTPUT_DIR", BASE.parent / "output"))
OUTPUT.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, static_folder=str(BASE / "static"), template_folder=str(BASE / "templates"))

JOBS = {}
LOCK = threading.Lock()


def _run_job(job_id, topic, duration, lang):
    job = JOBS[job_id]
    workdir = OUTPUT / job_id
    workdir.mkdir(parents=True, exist_ok=True)
    try:
        job["status"] = "writing_script"
        script = generate_script(topic, duration)
        job["script"] = script
        job["scenes_total"] = len(script)

        job["status"] = "generating_voiceover"
        audio_paths = []
        for i, line in enumerate(script):
            p = workdir / f"scene_{i:03d}.mp3"
            synthesize(line, p, lang=lang)
            audio_paths.append(p)
            job["scenes_done"] = i + 1

        job["status"] = "rendering_video"
        out = workdir / "video.mp4"
        render_video(script, audio_paths, out)
        job["status"] = "done"
        job["video_url"] = f"/files/{job_id}/video.mp4"
    except Exception as e:
        traceback.print_exc()
        job["status"] = "error"
        job["error"] = str(e)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/generate")
def generate():
    topic = (request.form.get("topic") or "").strip()
    if not topic or len(topic) > 300:
        return jsonify(error="Topic must be 1-300 characters."), 400
    try:
        duration = max(2, min(5, int(request.form.get("duration", 3))))
    except ValueError:
        duration = 3
    lang = request.form.get("lang", "en")
    job_id = uuid.uuid4().hex[:12]
    with LOCK:
        JOBS[job_id] = {
            "status": "queued", "topic": topic, "duration": duration, "lang": lang,
            "scenes_done": 0, "scenes_total": 0,
        }
    threading.Thread(target=_run_job, args=(job_id, topic, duration, lang), daemon=True).start()
    return jsonify(job_id=job_id)


@app.get("/api/status/<job_id>")
def status(job_id):
    job = JOBS.get(job_id)
    if not job:
        abort(404)
    return jsonify(job)


@app.get("/files/<job_id>/<path:filename>")
def files(job_id, filename):
    folder = OUTPUT / job_id
    if not folder.exists():
        abort(404)
    return send_from_directory(folder, filename)


@app.get("/api/download/<job_id>")
def download(job_id):
    folder = OUTPUT / job_id
    p = folder / "video.mp4"
    if not p.exists():
        abort(404)
    return send_from_directory(folder, "video.mp4", as_attachment=True,
                               download_name=f"sketch-{job_id}.mp4")


@app.get("/healthz")
def healthz():
    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
