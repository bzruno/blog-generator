"""Lista de artigos ordenada por data."""

def render(categories, posts, **kwargs):
    """Gera lista HTML de artigos (mais recente primeiro)."""
    items = [
        f'<li><span class="article-date">{p["formatted_date"]}</span> - '
        f'<a href="{p["url"]}">{p["title"]}</a></li>'
        for p in sorted(posts, key=lambda x: x.get("timestamp"), reverse=True)
    ]
    return f'<ul class="article-list">{"".join(items)}</ul>'