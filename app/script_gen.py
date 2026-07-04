"""AI script generation with Groq free API + template fallback."""
import os
import requests

SYSTEM_PROMPT = """You are a YouTube script writer for pencil-sketch explainer videos.
Write clear, engaging narration split into short scenes.
Return ONLY the narration text, one scene per line, no scene labels, no markdown.
Each line = one visual scene (~10-15 seconds of narration).
Hook viewers in the first line. End with a call to like/subscribe."""


def _target_line_count(duration_min: int) -> int:
    return max(8, int(duration_min * 60 / 12))


def generate_with_groq(topic: str, duration_min: int, api_key: str) -> list:
    n_lines = _target_line_count(duration_min)
    prompt = (
        f"Topic: {topic}\n"
        f"Target duration: {duration_min} minutes ({n_lines} scenes).\n"
        f"Write exactly {n_lines} narration lines."
    )
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "llama-3.1-8b-instant",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
        },
        timeout=60,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"].strip()
    lines = [ln.strip("-•* \t") for ln in text.splitlines() if ln.strip()]
    return lines[:n_lines] if len(lines) >= 4 else _template_script(topic, duration_min)


def _template_script(topic: str, duration_min: int) -> list:
    n = _target_line_count(duration_min)
    intro = [
        f"Have you ever wondered about {topic}? Stick around — you're about to find out.",
        f"In the next few minutes we'll break down {topic} in the simplest way possible.",
        f"Let's start with the basics of {topic}.",
    ]
    body = [
        f"First, it helps to know why {topic} matters in everyday life.",
        f"The core idea behind {topic} is surprisingly simple once you see it drawn out.",
        f"Here's how {topic} actually works, step by step.",
        f"One common misconception about {topic} is worth clearing up right now.",
        f"Real-world examples of {topic} are all around us.",
        f"Experts studying {topic} have found some fascinating patterns.",
        f"Let's look at what happens when {topic} goes wrong — and why.",
        f"There's also a bright side to {topic} that most people miss.",
        f"Putting it all together, {topic} comes down to a few key ideas.",
    ]
    outro = [
        f"So that's {topic}, explained in the simplest way we know how.",
        "If this helped you, smash that like button and subscribe for more.",
        "Thanks for watching — see you in the next one!",
    ]
    script = intro + body + outro
    while len(script) < n:
        script.insert(-3, f"Another important angle on {topic} is worth pausing on.")
    return script[:n]


def generate_script(topic: str, duration_min: int) -> list:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        try:
            return generate_with_groq(topic, duration_min, key)
        except Exception as e:
            print(f"[script] Groq failed, using template: {e}")
    return _template_script(topic, duration_min)
