from typing import List, Dict

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    """Gera HTML para lista de páginas avulsas, sem categorias e sem série."""
    
    page_list = [
        f'<li><a href="{p["url"]}">{p["title"]}</a></li>'
        for p in sorted(posts, key=lambda x: x["title"])
        if not p.get("is_article", False) and not p.get("categories", []) and not p.get("series", "")
    ]
    
    return f'<ul class="page-list">{"".join(page_list)}{content}</ul>'