"""Lista de páginas avulsas (não-artigos)."""

def render(categories, posts, **kwargs):
    """Gera lista HTML de páginas ordenadas alfabeticamente."""
    items = [
        f'<li><a href="{p["url"]}">{p["title"]}</a></li>'
        for p in sorted(posts, key=lambda x: x["title"])
        if not p.get("is_article", False)
    ]
    return f'<ul class="page-list">{"".join(items)}</ul>'