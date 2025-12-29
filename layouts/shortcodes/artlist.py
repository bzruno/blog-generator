from typing import List, Dict
from datetime import datetime
import logging

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    """Gera HTML para lista de artigos, incluindo apenas posts que são artigos, ordenados do mais novo ao mais antigo."""
    def parse_date(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                return datetime.strptime(date_str, "%d - %b - %Y")
            except ValueError:
                logging.warning(f"Formato de data inválido: {date_str}. Usando data atual.")
                return datetime.now()
    
    # Filtra apenas artigos e ordena por data (do mais novo ao mais antigo)
    sorted_articles = sorted(
        [p for p in posts if p.get("is_article", False)],
        key=lambda x: parse_date(x["date"]),
        reverse=True
    )
    
    # Gera a lista HTML com data no formato DD - MMM - YYYY
    items = [
        f'<li><span class="article-date">{p["formatted_date"]}</span> - <a href="{p["url"]}">{p["title"]}</a></li>'
        for p in sorted_articles
    ]
    return f'<ul class="article-list">{"".join(items)}{content}</ul>'