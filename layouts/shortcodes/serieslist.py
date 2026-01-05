from typing import List, Dict
import unicodedata
import re

def normalize(text):
    if not text:
        return ""
    normalized = unicodedata.normalize('NFKD', str(text))
    ascii_text = ''.join(c for c in normalized if not unicodedata.combining(c))
    return re.sub(r'-{2,}', '-', re.sub(r'[<>:"/\\|?*%\s]+', '-', ascii_text.lower())).strip('-')

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    series = sorted(set(p["series"] for p in posts if p.get("series", "")))
    series_list = ''.join(f'<li><a href="/series/{normalize(s)}">{s}</a></li>' for s in series)
    return f'<ul class="series-list">{series_list}{content}</ul>'