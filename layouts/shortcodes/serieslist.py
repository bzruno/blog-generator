"""Lista de séries disponíveis."""
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
    """Gera lista HTML de séries."""
    series = sorted(set(p["series"] for p in posts if p.get("series")))
    items = [
        f'<li><a href="/series/{normalize(s)}">{s}</a></li>'
        for s in series
    ]
    return f'<ul class="series-list">{"".join(items)}</ul>'