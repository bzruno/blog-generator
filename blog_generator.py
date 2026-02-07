#!/usr/bin/env python3
import re, shutil, subprocess, importlib.util, unicodedata, hashlib, time
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

# Raiz do projeto (permite rodar de qualquer diretório)
ROOT = Path(__file__).resolve().parent

# =============================================================================
# UTILS
# =============================================================================

def normalize(text):
    """Remove acentos e cria slug"""
    if not text: return ""
    nfd = unicodedata.normalize('NFD', str(text))
    slug = re.sub(r'[^\w\s-]', '', ''.join(c for c in nfd if not unicodedata.combining(c)).lower())
    return re.sub(r'[-\s]+', '-', slug).strip('-')

def format_date(date):
    """DD - Mês - YYYY"""
    return f"{date.day:02d} - {['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'][date.month-1]} - {date.year}"

def _parse_frontmatter_simple(lines, end_i):
    """Fallback: extrai frontmatter linha a linha (valores com ':' no texto podem quebrar)."""
    fm = {}
    for line in lines[1:end_i]:
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm


def parse_frontmatter(content):
    """Extrai YAML frontmatter. Usa PyYAML se disponível, senão parser simples."""
    lines = content.strip().splitlines()
    if not lines or lines[0] != "---":
        return {}, content

    for i, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            yaml_block = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:]).strip()
            try:
                import yaml
                fm = yaml.safe_load(yaml_block) or {}
            except Exception:
                fm = _parse_frontmatter_simple(lines, i)
            return fm, body
    return {}, content

def render_markdown(md):
    """Renderiza markdown via Node.js"""
    gfm_script = ROOT / "gfm.js"
    try:
        if subprocess.run(["node", "--version"], capture_output=True, timeout=5).returncode != 0:
            raise RuntimeError("Node.js não está instalado")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        raise RuntimeError("Node.js não encontrado ou timeout")

    if not gfm_script.exists():
        raise RuntimeError("Arquivo gfm.js não encontrado")

    try:
        result = subprocess.run(
            ["node", str(gfm_script)],
            input=md,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
            cwd=str(ROOT),
        )
        if result.returncode != 0:
            raise RuntimeError(f"Erro ao processar markdown: {result.stderr}")
        return result.stdout
    except subprocess.TimeoutExpired:
        raise RuntimeError("Timeout ao processar markdown (>30s)")

def load_shortcodes():
    """Carrega shortcodes de layouts/shortcodes/"""
    shortcodes, sc_dir = {}, ROOT / "layouts" / "shortcodes"
    if not sc_dir.exists():
        return shortcodes
    
    for file in sc_dir.glob("*.py"):
        if file.stem == "__init__": continue
        try:
            spec = importlib.util.spec_from_file_location(file.stem, file)
            mod = importlib.util.module_from_spec(spec)
            mod.__dict__['normalize'] = normalize
            spec.loader.exec_module(mod)
            if hasattr(mod, "render"):
                shortcodes[file.stem] = mod.render
        except Exception as e:
            raise RuntimeError(f"Falha ao carregar shortcode {file.stem}: {e}")
    return shortcodes

def process_shortcodes(content, shortcodes, categories, posts):
    """Substitui {{< shortcode >}} por HTML"""
    if not shortcodes or '{{<' not in content: return content
    
    def replace(m, inner=None):
        tag = (m.groups()[0] if inner is None else m.group(1)).strip()
        name = tag.split()[0]
        if name not in shortcodes: return m.group(0)
        try:
            return shortcodes[name](categories, posts)
        except Exception as e:
            raise RuntimeError(f"Erro ao processar shortcode '{name}': {e}")
    
    content = re.sub(r'{{<\s*([^/>]+?)\s*>}}(.*?){{<\s*/\1\s*>}}', 
                    lambda m: replace(m, True), content, flags=re.DOTALL)
    return re.sub(r'{{<\s*([^/>]+?)\s*>}}', replace, content)

# =============================================================================
# BUILDER
# =============================================================================

def load_content_file(filepath, is_article=True):
    """Carrega arquivo markdown e retorna dados estruturados"""
    fm, md = parse_frontmatter(filepath.read_text(encoding="utf-8"))
    date_val = fm.get("date")
    if date_val is None:
        date_obj = datetime.now()
    else:
        date_str = str(date_val)[:10]
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")

    series = fm.get("series") or ""
    clean_title = normalize(filepath.stem)

    cat_raw = fm.get("category", "Sem Categoria")
    if isinstance(cat_raw, list):
        categories_list = [str(c).strip() for c in cat_raw if str(c).strip()]
        category_str = ", ".join(categories_list) if categories_list else "Sem Categoria"
    else:
        category_str = str(cat_raw)
        categories_list = [c.strip() for c in category_str.split(",") if c.strip()] or ["Sem Categoria"]

    page_data = {
        "title": str(fm.get("title") or filepath.stem.replace("-", " ").title()),
        "subtitle": str(fm.get("subtitle") or ""),
        "raw_content": md,
        "timestamp": date_obj,
        "is_article": is_article,
        "categories": [],
    }

    if is_article:
        page_data.update({
            "date": date_obj.strftime("%Y-%m-%d"),
            "formatted_date": format_date(date_obj),
            "categories": categories_list,
            "category": category_str,
            "series": series,
            "part": int(fm.get("part", 0)) if series else 0,
            "output": f"series/{normalize(series)}/{clean_title}" if series else f"artigos/{clean_title}",
            "url": f"/series/{normalize(series)}/{clean_title}" if series else f"/artigos/{clean_title}"
        })
    else:
        page_data.update({"output": clean_title, "url": f"/{clean_title}"})
    
    return page_data

def build_site():
    """Gera site estático"""
    output_dir = ROOT / "public"
    
    # Limpa output mantendo .git e CNAME
    if output_dir.exists():
        (output_dir / "index.html").write_text(
            "<!DOCTYPE html><html><head><meta charset='utf-8'><meta http-equiv='refresh' content='1'></head>"
            "<body><p>Gerando site...</p></body></html>", encoding="utf-8")
        
        for item in output_dir.iterdir():
            if item.name not in [".git", "CNAME", "index.html"]:
                try:
                    (shutil.rmtree if item.is_dir() else item.unlink)(item)
                except Exception as e:
                    print(f"Aviso: não foi possível remover {item}: {e}")
    output_dir.mkdir(exist_ok=True)
    
    # Configuração
    env = Environment(loader=FileSystemLoader(str(ROOT / "layouts")))
    env.filters['normalize'] = normalize
    shortcodes = load_shortcodes()

    # Carrega conteúdo
    pages = []
    for dir_path in [ROOT / "content" / "articles", ROOT / "content" / "series"]:
        if dir_path.exists():
            pages.extend(load_content_file(f, True) for f in dir_path.rglob("*.md"))

    for filepath in (ROOT / "content").glob("*.md"):
        if filepath.name != "_index.md":
            pages.append(load_content_file(filepath, False))

    # Processa index
    index_file = ROOT / "content" / "_index.md"
    if not index_file.exists():
        raise RuntimeError("Arquivo content/_index.md não encontrado")
    fm, md = parse_frontmatter(index_file.read_text(encoding="utf-8"))
    
    # Organiza conteúdo
    pages.sort(key=lambda x: x["timestamp"], reverse=True)
    articles = [p for p in pages if p["is_article"]]
    pages_avulsas = [p for p in pages if not p["is_article"]]
    all_categories = sorted(set(cat for p in articles for cat in p["categories"]))
    
    # Renderiza páginas individuais
    for page in pages:
        page["content"] = render_markdown(process_shortcodes(page["raw_content"], shortcodes, all_categories, pages))
        del page["raw_content"]
        output_path = output_dir / page["output"] / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(env.get_template("page.html").render(**page), encoding="utf-8")
    
    # Homepage
    (output_dir / "index.html").write_text(
        env.get_template("page.html").render(
            title=str(fm.get("title") or "Página Inicial"),
            content=render_markdown(process_shortcodes(md, shortcodes, all_categories, pages)),
            is_article=False,
            is_homepage=True,
        ), encoding="utf-8"
    )
    
    # Páginas especiais
    for shortcode_name, data, title, path in [
        ("pagelist", pages_avulsas, "Páginas", "paginas"),
        ("artlist", articles, "Artigos", "artigos"),
        ("serieslist", articles, "Séries", "series")
    ]:
        if shortcode_name in shortcodes:
            p = output_dir / path / "index.html"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(env.get_template("page.html").render(
                title=title, content=shortcodes[shortcode_name]([], data), is_article=False
            ), encoding="utf-8")
    
    # Categorias
    if all_categories and "category" in shortcodes:
        path = output_dir / "categorias" / "index.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(env.get_template("page.html").render(
            title="Categorias", content=shortcodes["category"](all_categories, articles), is_article=False
        ), encoding="utf-8")
        
        if "artlist" in shortcodes:
            for cat in all_categories:
                cat_posts = [p for p in articles if cat in p["categories"]]
                if cat_posts:
                    p = output_dir / "categorias" / normalize(cat) / "index.html"
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(env.get_template("page.html").render(
                        title=cat, content=shortcodes["artlist"]([cat], cat_posts),
                        is_article=False, category_id=f"tag_{normalize(cat)}"
                    ), encoding="utf-8")
    
    # Séries
    series_list = sorted(set(p["series"] for p in articles if p["series"]))
    if series_list and "artlist" in shortcodes:
        for serie in series_list:
            posts = sorted([p for p in articles if p["series"] == serie], 
                         key=lambda x: (x["part"], x["timestamp"]))
            if posts:
                p = output_dir / "series" / normalize(serie) / "index.html"
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(env.get_template("page.html").render(
                    title=serie, content=shortcodes["artlist"]([], posts), is_article=False
                ), encoding="utf-8")
    
    # 404 e assets
    (output_dir / "404.html").write_text(env.get_template("404.html").render(), encoding="utf-8")
    
    for name in ["static", "images"]:
        src = ROOT / name
        if src.exists():
            dest = output_dir / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)

# =============================================================================
# WATCH MODE
# =============================================================================

def get_files_hash():
    """Calcula hash de todos os arquivos relevantes (inclui gfm.js e este script para o watch)."""
    hash_md5 = hashlib.md5()
    for directory in ["content", "layouts", "static", "images"]:
        dir_path = ROOT / directory
        if not dir_path.exists():
            continue
        for filepath in dir_path.rglob("*"):
            if filepath.is_file() and not any(x in str(filepath) for x in ['__pycache__', '.pyc', 'public']):
                try:
                    hash_md5.update(str(filepath).encode() + filepath.read_bytes())
                except (PermissionError, OSError) as e:
                    print(f"Aviso: não foi possível ler {filepath}: {e}")
    for single in [ROOT / "gfm.js", ROOT / "blog_generator.py"]:
        if single.exists():
            try:
                hash_md5.update(str(single).encode() + single.read_bytes())
            except (PermissionError, OSError) as e:
                print(f"Aviso: não foi possível ler {single}: {e}")
    return hash_md5.hexdigest()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "watch":
        print("Construindo site inicial...")
        build_site()
        print("✓ Site gerado")
        
        last_hash = get_files_hash()
        print("Monitorando mudanças (Ctrl+C para sair)...")
        
        try:
            while True:
                time.sleep(2)
                current_hash = get_files_hash()
                if current_hash != last_hash:
                    print("Mudança detectada, reconstruindo...")
                    try:
                        build_site()
                        print("✓ Site gerado")
                        last_hash = current_hash
                    except Exception as e:
                        print(f"✗ Erro ao gerar site: {e}")
        except KeyboardInterrupt:
            print("\nMonitoramento encerrado")
    else:
        build_site()
        print("Site gerado")