# Sketch Explainer — Flask backend

Free, self-hosted **pencil-sketch YouTube explainer video** generator.
Flask + gTTS + OpenCV + MoviePy. One-click deploy to Render.

## One-click Render deploy
1. Push this folder to a GitHub repo (public or private).
2. Go to https://render.com → **New → Blueprint** → connect the repo.
3. Render reads `render.yaml` and builds automatically.
4. In the Render dashboard for the service, open **Environment** and set:
   - `GROQ_API_KEY` = your Groq key (get free at https://console.groq.com/keys)
5. Wait for the first build (~5 min). Open the `.onrender.com` URL. Done.

Without `GROQ_API_KEY`, the app still works using a built-in template script generator.

## Local run
```bash
pip install -r requirements.txt
export GROQ_API_KEY=your_key_here   # optional
python -m app.main
```
Open http://localhost:10000

## How to use
1. Enter a topic (e.g. "How photosynthesis works")
2. Pick duration (2–5 min) + voice language
3. Click **Generate video** — wait 1–3 min
4. Preview and download the MP4
5. Upload to your YouTube channel

## Notes
- Render's free tier sleeps after 15 min inactivity and has 512 MB RAM. For longer videos or heavy use, upgrade to Starter ($7/mo).
- All dependencies are free & open source.
- No YouTube upload automation — download and upload manually (safest for monetization).

## Structure
```
app/
  main.py          # Flask app + endpoints
  script_gen.py    # Groq API + template fallback
  tts.py           # gTTS voiceover
  video_render.py  # OpenCV pencil-sketch + MoviePy
  templates/index.html
  static/style.css, app.js
Dockerfile
render.yaml
requirements.txt
```
