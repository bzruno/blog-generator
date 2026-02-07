# category.py
"""Lista de categorias com links."""
def render(categories, _):
    items = ''.join(f'<li><a id="tag_{normalize(c)}" href="/categorias/{normalize(c)}">{c}</a></li>' 
                    for c in sorted(categories))
    return f'<ul class="category-list">{items}</ul>'