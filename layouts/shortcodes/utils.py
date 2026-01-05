import unicodedata
import re

def normalize(text):
    """Normaliza texto para URLs, removendo acentos e caracteres inválidos."""
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', str(text))
    ascii_text = ''.join(c for c in normalized if not unicodedata.combining(c))
    return re.sub(r'-{2,}', '-', re.sub(r'[<>:"/\\|?*%\s]+', '-', ascii_text.lower())).strip('-')