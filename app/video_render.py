"""Pencil-sketch / whiteboard-style video renderer."""
import numpy as np
import cv2
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import AudioFileClip, ImageSequenceClip, concatenate_videoclips

W, H = 1280, 720
FPS = 15
PAPER_COLOR = (250, 247, 235)
INK_COLOR = (30, 30, 30)


def _paper_bg() -> np.ndarray:
    bg = np.full((H, W, 3), PAPER_COLOR, dtype=np.uint8)
    noise = np.random.randint(0, 8, (H, W, 1), dtype=np.uint8)
    return np.clip(bg.astype(int) - noise, 0, 255).astype(np.uint8)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _sketchify(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    inv = 255 - gray
    blur = cv2.GaussianBlur(inv, (21, 21), 0)
    sketch = cv2.divide(gray, 255 - blur, scale=256)
    return cv2.cvtColor(sketch, cv2.COLOR_GRAY2RGB)


def _wrap_text(text: str, font, max_width: int) -> list:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _render_scene_frames(text: str, duration_s: float, scene_idx: int) -> list:
    font_size = 48 if len(text) < 120 else 38
    font = _load_font(font_size)
    small_font = _load_font(22)
    wrapped = _wrap_text(text, font, W - 200)

    base = _paper_bg()
    base_pil = Image.fromarray(base)
    draw = ImageDraw.Draw(base_pil)
    draw.text((40, 30), f"Scene {scene_idx + 1}", font=small_font, fill=(120, 120, 120))
    draw.line([(40, 62), (W - 40, 62)], fill=(180, 180, 180), width=2)
    base = np.array(base_pil)

    full_pil = Image.fromarray(base.copy())
    d = ImageDraw.Draw(full_pil)
    total_h = sum(font.getbbox(l)[3] - font.getbbox(l)[1] + 18 for l in wrapped)
    y = (H - total_h) // 2
    for line in wrapped:
        bbox = font.getbbox(line)
        w = bbox[2] - bbox[0]
        x = (W - w) // 2
        d.text((x, y), line, font=font, fill=INK_COLOR)
        y += bbox[3] - bbox[1] + 18
    full = np.array(full_pil)
    full_sketch = _sketchify(full)
    full_final = np.where(full_sketch < 200, full_sketch, base)

    n_frames = max(int(duration_s * FPS), 6)
    reveal_frames = int(n_frames * 0.85)
    hold_frames = n_frames - reveal_frames

    frames = []
    for i in range(reveal_frames):
        progress = (i + 1) / reveal_frames
        cutoff = int(W * progress)
        frame = base.copy()
        frame[:, :cutoff] = full_final[:, :cutoff]
        if cutoff < W - 5:
            cv2.circle(frame, (cutoff, H // 2), 6, (60, 60, 60), -1)
            cv2.line(frame, (cutoff, H // 2), (cutoff + 25, H // 2 - 40), (60, 60, 60), 2)
        frames.append(frame)
    for _ in range(hold_frames):
        frames.append(full_final)
    return frames


def render_video(script_lines: list, audio_paths: list, out_path: Path) -> Path:
    clips, audios = [], []
    for idx, (line, audio_path) in enumerate(zip(script_lines, audio_paths)):
        audio = AudioFileClip(str(audio_path))
        duration = max(audio.duration, 2.0)
        frames = _render_scene_frames(line, duration, idx)
        clip = ImageSequenceClip(frames, fps=FPS).set_duration(duration).set_audio(audio)
        clips.append(clip)
        audios.append(audio)
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        str(out_path), fps=FPS, codec="libx264", audio_codec="aac",
        preset="ultrafast", threads=2, logger=None,
    )
    for a in audios:
        a.close()
    final.close()
    return out_path
