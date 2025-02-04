from .config import Config
from datetime import datetime

def classify_content(text):
    text_lower = text.lower()
    for category, keywords in Config.CONTENT_CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    return 'other'