# processors/language_detector.py

def detect_language(text: str) -> str:
    if not text:
        return "en"

    fa_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
    ratio = fa_chars / len(text)
    return "fa" if ratio > 0.1 else "en"