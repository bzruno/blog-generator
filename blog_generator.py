#!/usr/bin/env python3
import re, shutil, subprocess, importlib.util
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# =============================================================================
# UTILS
# =============================================================================

def normalize(text):
    """Remove acentos e cria slug"""
    import unicodedata
    nfd = unicodedata.normalize('NFD', str(text))
    ascii_text = ''.join(c for c in nfd if not unicodedata.combining(c))
    slug = re.sub(r'[^\w\s-]', '', ascii_text.lower())
    return re.sub(r'[-\s]+', '-', slug).strip('-')

def format_date(date):
    """Formata data: DD - Mês - YYYY"""
    months = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    return f"{date.day:02d} - {months[date.month-1]} - {date.year}"

def parse_frontmatter(content):
    """Extrai YAML frontmatter"""
    lines = content.strip().splitlines()
    if not lines or lines[0] != "---":
        return {}, content
    
    fm = {}
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return fm, "\n".join(lines[i+1:]).strip()
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return {}, content

def render_markdown(md):
    """Renderiza markdown via Node.js"""
    result = subprocess.run(
        ["node", "gfm.js"],
        input=md,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"Markdown error: {result.stderr}")
    return result.stdout

# =============================================================================
# SHORTCODES
# =============================================================================

def load_shortcodes():
    """Carrega módulos Python de layouts/shortcodes/"""
    shortcodes = {}
    sc_dir = Path("layouts/shortcodes")
    
    if not sc_dir.exists():
        return shortcodes
    
    for file in sc_dir.glob("*.py"):
        if file.stem == "__init__":
            continue
        spec = importlib.util.spec_from_file_location(file.stem, file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "render"):
            shortcodes[file.stem] = mod.render
    
    return shortcodes

def process_shortcodes(content, shortcodes, categories, posts):
    """Substitui {{< shortcode >}} por HTML"""
    if not shortcodes or '{{<' not in content:
        return content
    
    def parse_args(text):
        return {m[0]: m[2] for m in re.finditer(r'(\w+)=(["\']?)([^"\'\s]+)\2', text or "")}
    
    # Paired: {{< name >}}...{{< /name >}}
    def replace_paired(m):
        tag, inner = m.groups()
        parts = tag.split(None, 1)
        name = parts[0]
        if name not in shortcodes:
            return m.group(0)
        args = parse_args(parts[1] if len(parts) > 1 else "")
        return shortcodes[name](categories, posts, content=inner, **args)
    
    content = re.sub(
        r'{{<\s*([^/>]+?)\s*>}}(.*?){{<\s*/\1\s*>}}',
        replace_paired,
        content,
        flags=re.DOTALL
    )
    
    # Simple: {{< name >}}
    def replace_simple(m):
        tag = m.group(1).strip()
        parts = tag.split(None, 1)
        name = parts[0]
        if name not in shortcodes:
            return m.group(0)
        args = parse_args(parts[1] if len(parts) > 1 else "")
        return shortcodes[name](categories, posts, **args)
    
    return re.sub(r'{{<\s*([^/>]+?)\s*>}}', replace_simple, content)

# =============================================================================
# BUILDER
# =============================================================================

def build_site():
    """Gera site estático"""
    
    # Setup
    content_dir = Path("content")
    layouts_dir = Path("layouts")
    output_dir = Path("public")
    
    # Reset public/ preservando .git e mantendo index.html temporário
    if output_dir.exists():
        # Cria index.html temporário ANTES de limpar
        temp_index = output_dir / "index.html"
        temp_index.write_text("<!DOCTYPE html><html><head><meta charset='utf-8'></head><body></body></html>", encoding="utf-8")
        
        # Limpa tudo exceto .git e index.html
        for item in output_dir.iterdir():
            if item.name not in [".git", "index.html"]:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
    
    output_dir.mkdir(exist_ok=True)
    
    # Jinja2
    env = Environment(loader=FileSystemLoader(layouts_dir))
    env.filters['normalize'] = normalize
    
    # Shortcodes
    shortcodes = load_shortcodes()
    
    # =============================================================================
    # LOAD CONTENT
    # =============================================================================
    
    pages = []
    
    # Artigos e séries
    for dir_path in [content_dir / "articles", content_dir / "series"]:
        if dir_path.exists():
            for filepath in dir_path.rglob("*.md"):
                content = filepath.read_text(encoding="utf-8")
                fm, md = parse_frontmatter(content)
                
                title = fm.get("title", filepath.stem.replace("-", " ").title())
                series = fm.get("series", "")
                date_str = fm.get("date", datetime.now().strftime("%Y-%m-%d"))
                
                try:
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    date_obj = datetime.now()
                    date_str = date_obj.strftime("%Y-%m-%d")
                
                category_str = fm.get("category", "Sem Categoria")
                categories = [c.strip() for c in category_str.split(",") if c.strip()]
                
                # URL - sempre em artigos/ a menos que tenha series no frontmatter
                clean_title = normalize(filepath.stem)
                if series:
                    output = f"series/{normalize(series)}/{clean_title}"
                else:
                    output = f"artigos/{clean_title}"
                
                pages.append({
                    "title": title,
                    "subtitle": fm.get("subtitle", ""),
                    "date": date_str,
                    "timestamp": date_obj,
                    "formatted_date": format_date(date_obj),
                    "categories": categories,
                    "category": category_str,
                    "series": series,
                    "part": int(fm.get("part", 0)) if series else 0,
                    "raw_content": md,
                    "output": output,
                    "url": f"/{output}",
                    "is_article": True
                })
    
    # Páginas avulsas
    for filepath in content_dir.glob("*.md"):
        if filepath.name != "_index.md":
            content = filepath.read_text(encoding="utf-8")
            fm, md = parse_frontmatter(content)
            
            title = fm.get("title", filepath.stem.replace("-", " ").title())
            clean_title = normalize(filepath.stem)
            
            pages.append({
                "title": title,
                "subtitle": "",
                "raw_content": md,
                "output": clean_title,
                "url": f"/{clean_title}",
                "is_article": False,
                "categories": [],
                "timestamp": datetime.now()
            })
    
    # Index
    index_path = content_dir / "_index.md"
    if not index_path.exists():
        raise FileNotFoundError("_index.md não encontrado")
    
    content = index_path.read_text(encoding="utf-8")
    fm, md = parse_frontmatter(content)
    index_page = {"title": fm.get("title", "Página Inicial"), "raw_content": md}
    
    # Ordena por data
    pages.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # =============================================================================
    # PROCESS
    # =============================================================================
    
    articles = [p for p in pages if p["is_article"]]
    all_categories = sorted(set(cat for p in articles for cat in p["categories"]))
    
    # Páginas individuais
    for page in pages:
        content_with_shortcodes = process_shortcodes(
            page["raw_content"], 
            shortcodes, 
            all_categories, 
            articles
        )
        html = render_markdown(content_with_shortcodes)
        page["content"] = html
        
        rendered = env.get_template("page.html").render(**page)
        output_path = output_dir / page["output"] / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    
    # Index
    content_with_shortcodes = process_shortcodes(
        index_page["raw_content"], 
        shortcodes, 
        all_categories, 
        articles
    )
    html_content = render_markdown(content_with_shortcodes)
    
    rendered = env.get_template("page.html").render(
        title=index_page["title"],
        content=html_content,
        is_article=False,
        is_homepage=True
    )
    (output_dir / "index.html").write_text(rendered, encoding="utf-8")
    
    # Páginas especiais
    pages_avulsas = [p for p in pages if not p["is_article"]]
    
    if "pagelist" in shortcodes:
        content = shortcodes["pagelist"]([], pages_avulsas)
        rendered = env.get_template("page.html").render(
            title="Páginas",
            content=content,
            is_article=False
        )
        path = output_dir / "paginas" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    
    if "artlist" in shortcodes:
        content = shortcodes["artlist"]([], articles)
        rendered = env.get_template("page.html").render(
            title="Artigos",
            content=content,
            is_article=False
        )
        path = output_dir / "artigos" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    
    if "serieslist" in shortcodes:
        content = shortcodes["serieslist"]([], articles)
        rendered = env.get_template("page.html").render(
            title="Séries",
            content=content,
            is_article=False
        )
        path = output_dir / "series" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
    
    # Categorias
    if all_categories and "category" in shortcodes:
        content = shortcodes["category"](all_categories, articles)
        rendered = env.get_template("page.html").render(
            title="Categorias",
            content=content,
            is_article=False
        )
        path = output_dir / "categorias" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rendered, encoding="utf-8")
        
        # Páginas individuais de categoria
        if "artlist" in shortcodes:
            for cat in all_categories:
                cat_posts = [p for p in articles if cat in p["categories"]]
                if cat_posts:
                    content = shortcodes["artlist"]([cat], cat_posts)
                    rendered = env.get_template("page.html").render(
                        title=cat,
                        content=content,
                        is_article=False,
                        category_id=f"tag_{normalize(cat)}"
                    )
                    path = output_dir / "categorias" / normalize(cat) / "index.html"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(rendered, encoding="utf-8")
    
    # Séries individuais
    series_list = sorted(set(p["series"] for p in articles if p["series"]))
    if series_list and "artlist" in shortcodes:
        for serie in series_list:
            posts = sorted(
                [p for p in articles if p["series"] == serie],
                key=lambda x: (x["part"], x["timestamp"])
            )
            if posts:
                content = shortcodes["artlist"]([], posts)
                rendered = env.get_template("page.html").render(
                    title=serie,
                    content=content,
                    is_article=False
                )
                path = output_dir / "series" / normalize(serie) / "index.html"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rendered, encoding="utf-8")
    
    # 404
    rendered = env.get_template("404.html").render()
    (output_dir / "404.html").write_text(rendered, encoding="utf-8")
    
    # Copia estáticos
    for name in ["static", "images"]:
        src = Path(name)
        dest = output_dir / name
        if src.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)

if __name__ == "__main__":
    build_site()