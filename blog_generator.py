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
    """DD - Mês - YYYY"""
    months = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    return f"{date.day:02d} - {months[date.month-1]} - {date.year}"

def parse_frontmatter(content):
    """Extrai YAML frontmatter"""
    lines = content.strip().splitlines()
    if not lines or lines[0] != "---":
        return {}, content
    
    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            fm = {k.strip(): v.strip() for l in lines[1:i] if ":" in l for k, v in [l.split(":", 1)]}
            return fm, "\n".join(lines[i+1:]).strip()
    return {}, content

def render_markdown(md):
    """Renderiza markdown via Node.js"""
    result = subprocess.run(["node", "gfm.js"], input=md, capture_output=True, text=True, encoding="utf-8", timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"Markdown error: {result.stderr}")
    return result.stdout

def load_shortcodes():
    """Carrega shortcodes de layouts/shortcodes/"""
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
    
    # Paired shortcodes
    def replace_paired(m):
        tag, inner = m.groups()
        name = tag.split()[0]
        if name not in shortcodes:
            return m.group(0)
        args = parse_args(" ".join(tag.split()[1:])) if len(tag.split()) > 1 else {}
        return shortcodes[name](categories, posts, content=inner, **args)
    
    content = re.sub(r'{{<\s*([^/>]+?)\s*>}}(.*?){{<\s*/\1\s*>}}', replace_paired, content, flags=re.DOTALL)
    
    # Simple shortcodes
    def replace_simple(m):
        tag = m.group(1).strip()
        name = tag.split()[0]
        if name not in shortcodes:
            return m.group(0)
        args = parse_args(" ".join(tag.split()[1:])) if len(tag.split()) > 1 else {}
        return shortcodes[name](categories, posts, **args)
    
    return re.sub(r'{{<\s*([^/>]+?)\s*>}}', replace_simple, content)

# =============================================================================
# BUILDER
# =============================================================================

def load_content_file(filepath, is_article=True):
    """Carrega um arquivo markdown e retorna dados estruturados"""
    content = filepath.read_text(encoding="utf-8")
    fm, md = parse_frontmatter(content)
    
    date_obj = datetime.strptime(fm.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d") if "date" in fm else datetime.now()
    series = fm.get("series", "")
    clean_title = normalize(filepath.stem)
    
    page_data = {
        "title": fm.get("title", filepath.stem.replace("-", " ").title()),
        "subtitle": fm.get("subtitle", ""),
        "raw_content": md,
        "timestamp": date_obj,
        "is_article": is_article,
        "categories": []
    }
    
    if is_article:
        page_data.update({
            "date": date_obj.strftime("%Y-%m-%d"),
            "formatted_date": format_date(date_obj),
            "categories": [c.strip() for c in fm.get("category", "Sem Categoria").split(",") if c.strip()],
            "category": fm.get("category", "Sem Categoria"),
            "series": series,
            "part": int(fm.get("part", 0)) if series else 0,
            "output": f"series/{normalize(series)}/{clean_title}" if series else f"artigos/{clean_title}",
            "url": f"/series/{normalize(series)}/{clean_title}" if series else f"/artigos/{clean_title}"
        })
    else:
        page_data.update({
            "output": clean_title,
            "url": f"/{clean_title}"
        })
    
    return page_data

def build_site():
    """Gera site estático"""
    output_dir = Path("public")
    
    # Reset public/ (preserva .git)
    if output_dir.exists():
        # Cria index.html temporário ANTES de limpar para evitar directory listing
        temp_index = output_dir / "index.html"
        temp_index.write_text("<!DOCTYPE html><html><head><meta charset='utf-8'></head><body></body></html>", encoding="utf-8")
        
        # Limpa tudo exceto .git e index.html
        for item in output_dir.iterdir():
            if item.name not in [".git", "index.html"]:
                shutil.rmtree(item) if item.is_dir() else item.unlink()
    output_dir.mkdir(exist_ok=True)
    
    # Setup
    env = Environment(loader=FileSystemLoader("layouts"))
    env.filters['normalize'] = normalize
    shortcodes = load_shortcodes()
    
    # Carrega artigos e séries
    pages = []
    for dir_path in [Path("content/articles"), Path("content/series")]:
        if dir_path.exists():
            for filepath in dir_path.rglob("*.md"):
                pages.append(load_content_file(filepath, is_article=True))
    
    # Carrega páginas avulsas
    for filepath in Path("content").glob("*.md"):
        if filepath.name != "_index.md":
            pages.append(load_content_file(filepath, is_article=False))
    
    # Index
    index_content = (Path("content") / "_index.md").read_text(encoding="utf-8")
    fm, md = parse_frontmatter(index_content)
    
    # Organiza dados
    pages.sort(key=lambda x: x["timestamp"], reverse=True)
    articles = [p for p in pages if p["is_article"]]
    all_categories = sorted(set(cat for p in articles for cat in p["categories"]))
    
    # Renderiza todas as páginas
    for page in pages:
        page["content"] = render_markdown(process_shortcodes(page["raw_content"], shortcodes, all_categories, articles))
        output_path = output_dir / page["output"] / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(env.get_template("page.html").render(**page), encoding="utf-8")
    
    # Index
    (output_dir / "index.html").write_text(
        env.get_template("page.html").render(
            title=fm.get("title", "Página Inicial"),
            content=render_markdown(process_shortcodes(md, shortcodes, all_categories, articles)),
            is_article=False,
            is_homepage=True
        ),
        encoding="utf-8"
    )
    
    # Páginas especiais (páginas, artigos, séries)
    pages_avulsas = [p for p in pages if not p["is_article"]]
    for shortcode_name, data, title, path in [
        ("pagelist", pages_avulsas, "Páginas", "paginas"),
        ("artlist", articles, "Artigos", "artigos"),
        ("serieslist", articles, "Séries", "series"),
    ]:
        if shortcode_name in shortcodes:
            output_path = output_dir / path / "index.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                env.get_template("page.html").render(title=title, content=shortcodes[shortcode_name]([], data), is_article=False),
                encoding="utf-8"
            )
    
    # Categorias
    if all_categories and "category" in shortcodes:
        # Página de todas as categorias
        path = output_dir / "categorias" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            env.get_template("page.html").render(title="Categorias", content=shortcodes["category"](all_categories, articles), is_article=False),
            encoding="utf-8"
        )
        
        # Página individual de cada categoria
        if "artlist" in shortcodes:
            for cat in all_categories:
                cat_posts = [p for p in articles if cat in p["categories"]]
                if cat_posts:
                    path = output_dir / "categorias" / normalize(cat) / "index.html"
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(
                        env.get_template("page.html").render(
                            title=cat,
                            content=shortcodes["artlist"]([cat], cat_posts),
                            is_article=False,
                            category_id=f"tag_{normalize(cat)}"
                        ),
                        encoding="utf-8"
                    )
    
    # Séries individuais
    series_list = sorted(set(p["series"] for p in articles if p["series"]))
    if series_list and "artlist" in shortcodes:
        for serie in series_list:
            posts = sorted([p for p in articles if p["series"] == serie], key=lambda x: (x["part"], x["timestamp"]))
            if posts:
                path = output_dir / "series" / normalize(serie) / "index.html"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    env.get_template("page.html").render(title=serie, content=shortcodes["artlist"]([], posts), is_article=False),
                    encoding="utf-8"
                )
    
    # 404
    (output_dir / "404.html").write_text(env.get_template("404.html").render(), encoding="utf-8")
    
    # Copia estáticos
    for name in ["static", "images"]:
        src, dest = Path(name), output_dir / name
        if src.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
    
    # Copia .domains se existir
    domains_file = Path(".domains")
    if domains_file.exists():
        shutil.copy(domains_file, output_dir / ".domains")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        import time
        import hashlib
        
        def get_files_hash():
            hash_md5 = hashlib.md5()
            for directory in ["content", "layouts", "static", "images"]:
                dir_path = Path(directory)
                if not dir_path.exists():
                    continue
                for filepath in dir_path.rglob("*"):
                    if filepath.is_file() and not any(x in str(filepath) for x in ['__pycache__', '.pyc', 'public']):
                        try:
                            hash_md5.update(str(filepath).encode())
                            hash_md5.update(filepath.read_bytes())
                        except:
                            pass
            return hash_md5.hexdigest()
        
        build_site()
        print("Site gerado")
        
        last_hash = get_files_hash()
        
        try:
            while True:
                time.sleep(1)
                current_hash = get_files_hash()
                if current_hash != last_hash:
                    build_site()
                    print("Site gerado")
                    last_hash = current_hash
        except KeyboardInterrupt:
            pass
    else:
        build_site()
        print("Site gerado")