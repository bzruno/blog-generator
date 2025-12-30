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
    """Gera HTML para lista de categorias."""
    category_list = ''.join(
        f'<li><a id="tag_{_normalize_text(c)}" href="/categorias/{_normalize_text(c)}">{c}</a></li>'
        for c in sorted(categories)
    )
    return f'<ul class="category-list">{category_list}{content}</ul>'