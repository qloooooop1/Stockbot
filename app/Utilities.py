import re

class ContentFilter:
    def __init__(self):
        self.forbidden_patterns = [
            r'\d{10}',  # أرقام هواتف
            r'http[s]?://',  # روابط
            r'واتساب|واتس'  # كلمات ممنوعة
        ]

    def should_delete(self, text):
        return any(re.search(pattern, text) for pattern in self.forbidden_patterns)