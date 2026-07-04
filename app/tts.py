"""Free voiceover via gTTS."""
from gtts import gTTS
from pathlib import Path


def synthesize(text: str, out_path: Path, lang: str = "en") -> Path:
    tld = "com"
    if lang == "en-uk":
        lang, tld = "en", "co.uk"
    elif lang == "en-au":
        lang, tld = "en", "com.au"
    tts = gTTS(text=text, lang=lang, tld=tld, slow=False)
    tts.save(str(out_path))
    return out_path
