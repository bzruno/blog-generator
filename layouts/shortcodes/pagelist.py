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
    """Gera HTML para lista de páginas avulsas, sem categorias e sem série."""
    page_list = [
        f'<li><a href="/{_normalize_text(p["title"])}">{p["title"]}</a></li>'
        for p in sorted(posts, key=lambda x: x["title"])
        if not p.get("is_article", False) and not p.get("categories", []) and not p.get("series", "")
    ]
    return f'<ul class="page-list">{"".join(page_list)}{content}</ul>'