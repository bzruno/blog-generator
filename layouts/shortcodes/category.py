from typing import List, Dict
import unicodedata
import re

def _normalize_text(text: str) -> str:
    """Normaliza texto para URLs (idêntico a Utils.normalize)."""
    normalized = unicodedata.normalize('NFKD', text)
    ascii_text = ''.join(c for c in normalized if not unicodedata.combining(c))
    return re.sub(r'-{2,}', '-', re.sub(r'[<>:"/\\|?*%\s]+', '-', ascii_text.lower())).strip('-')

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    """Gera HTML para lista de categorias."""
    category_list = ''.join(
        f'<li><a id="tag_{_normalize_text(c)}" href="/categorias/{_normalize_text(c)}">{c}</a></li>'
        for c in sorted(categories)
    )
    return f'<ul class="category-list">{category_list}{content}</ul>'