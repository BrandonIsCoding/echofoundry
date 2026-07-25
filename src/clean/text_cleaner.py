"""Cleans transcript text."""

def clean_text(text):
    import re
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    return text.strip()
