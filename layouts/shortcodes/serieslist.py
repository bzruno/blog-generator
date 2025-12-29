from typing import List, Dict
import unicodedata
import re

def _normalize_text(text: str) -> str:
    """Normaliza texto para URLs, removendo acentos e caracteres inválidos."""
    text = text.replace('ç', 'c').replace('Ç', 'C')
    normalized = unicodedata.normalize('NFKD', text.lower())
    invalid_chars = r'[<>:"/\\|?*%]'
    cleaned = re.sub(invalid_chars, '', normalized)
    cleaned = ''.join(c for c in cleaned if not unicodedata.combining(c))
    return cleaned.replace(" ", "-").strip("-")

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    """Gera HTML para lista de séries."""
    series = sorted(set(p["series"] for p in posts if p["series"]))
    series_list = ''.join(
        f'<li><a href="/series/{_normalize_text(s)}">{s}</a></li>'
        for s in series
    )
    return f'<ul class="series-list">{series_list}{content}</ul>'