from typing import List, Dict
from bs4 import BeautifulSoup
import markdown

def render(categories: List[str], posts: List[Dict[str, str]], content: str = "", **kwargs) -> str:
    class_name = kwargs.get('class', 'default-class')
    # Converte o conteúdo Markdown para HTML
    inner_html = markdown.markdown(content, extensions=['extra'])
    # Usa BeautifulSoup para processar o HTML e adicionar o atributo data-shortcode
    soup = BeautifulSoup(inner_html, "html.parser")
    for img in soup.find_all("img"):
        img['data-shortcode'] = 'true'
    return f'<div class="{class_name}">{str(soup)}</div>'