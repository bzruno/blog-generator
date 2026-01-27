"""Lista de categorias com links."""
import unicodedata
import re

def normalize(text):
    """Remove acentos e cria slug"""
    if not text:
        return ""
    nfd = unicodedata.normalize('NFD', str(text))
    ascii_text = ''.join(c for c in nfd if not unicodedata.combining(c))
    slug = re.sub(r'[^\w\s-]', '', ascii_text.lower())
    return re.sub(r'[-\s]+', '-', slug).strip('-')

def render(categories, posts, **kwargs):
    """Gera lista HTML de categorias."""
    items = [
        f'<li><a id="tag_{normalize(c)}" href="/categorias/{normalize(c)}">{c}</a></li>'
        for c in sorted(categories)
    ]
    return f'<ul class="category-list">{"".join(items)}</ul>'