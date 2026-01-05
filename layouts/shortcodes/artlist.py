from typing import List, Dict
from datetime import datetime

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    """Gera HTML para lista de artigos, usando o timestamp pré-calculado."""
    
    # Filtra apenas artigos e ordena por timestamp
    sorted_articles = sorted(
        [p for p in posts if p.get("is_article", False)],
        key=lambda x: x.get("timestamp", datetime.min),
        reverse=True
    )
    
    items = [
        f'<li><span class="article-date">{p["formatted_date"]}</span> - <a href="{p["url"]}">{p["title"]}</a></li>'
        for p in sorted_articles
    ]
    
    return f'<ul class="article-list">{"".join(items)}{content}</ul>'