# artlist.py
"""Lista de artigos ordenada por data (mais recente primeiro)."""
def render(_, posts):
    items = ''.join(f'<li><span class="article-date">{p["formatted_date"]}</span> - '
                    f'<a href="{p["url"]}">{p["title"]}</a></li>'
                    for p in sorted((p for p in posts if p.get("is_article", False)), 
                                   key=lambda x: x.get("timestamp"), reverse=True))
    return f'<ul class="article-list">{items}</ul>'