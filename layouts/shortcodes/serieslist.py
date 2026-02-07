# serieslist.py
"""Lista de séries disponíveis."""
def render(_, posts):
    items = ''.join(f'<li><a href="/series/{normalize(s)}">{s}</a></li>'
                    for s in sorted(set(p["series"] for p in posts 
                                       if p.get("is_article", False) and p["series"])))
    return f'<ul class="series-list">{items}</ul>'