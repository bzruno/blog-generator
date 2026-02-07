# pagelist.py
"""Lista de páginas avulsas (não-artigos) ordenada alfabeticamente."""
def render(_, posts):
    items = ''.join(f'<li><a href="{p["url"]}">{p["title"]}</a></li>'
                    for p in sorted((p for p in posts if not p.get("is_article", False)), 
                                   key=lambda x: x.get("title", "")))
    return f'<ul class="page-list">{items}</ul>'