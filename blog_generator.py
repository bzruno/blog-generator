import sys, shutil, re, os, time, threading, unicodedata, importlib.util, subprocess
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from concurrent.futures import ThreadPoolExecutor
import http.server, socketserver
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ============================================================================
# CONFIGURAÇÃO
# ============================================================================

SITE_CONFIG = {
    'output_dir': 'public',
    'port': 8000,
    'markdown_timeout': 30,
    'enable_threading': False,  # Desabilitado para blogs pequenos
    'debounce_delay': 1.0,  # Segundos para debounce no live reload
}

# ============================================================================
# UTILIDADES
# ============================================================================

class Utils:
    MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]

    @staticmethod
    def normalize(text):
        if not text:
            return ""
        normalized = unicodedata.normalize('NFKD', str(text))
        ascii_text = ''.join(c for c in normalized if not unicodedata.combining(c))
        return re.sub(r'-+', '-', re.sub(r'[<>:"/\\|?*%\s]+', '-', ascii_text.lower())).strip('-')

    @staticmethod
    def parse_frontmatter(content):
        lines = content.strip().splitlines()
        if not lines or lines[0] != "---":
            return {"title": "Sem Título", "date": datetime.now().strftime("%Y-%m-%d")}, content

        fm, start = {}, 0
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                start = i + 1
                break
            if ":" in line:
                k, v = map(str.strip, line.split(":", 1))
                fm[k] = v

        return fm, "\n".join(lines[start:]).strip()

    @classmethod
    def format_date(cls, date):
        return f"{date.day:02d} - {cls.MONTHS[date.month-1]} - {date.year}"

# ============================================================================
# GFM RENDERER
# ============================================================================

def render_gfm(markdown_text: str) -> str:
    """Renderiza Markdown usando Node.js com markdown-it"""
    try:
        process = subprocess.Popen(
            ["node", "gfm.js"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )
        html, err = process.communicate(markdown_text, timeout=SITE_CONFIG['markdown_timeout'])
        if process.returncode != 0:
            raise RuntimeError(f"GFM Error: {err}")
        return html
    except subprocess.TimeoutExpired:
        process.kill()
        raise RuntimeError(f"GFM rendering timeout ({SITE_CONFIG['markdown_timeout']}s)")

# ============================================================================
# PROCESSADOR DE CONTEÚDO
# ============================================================================

class ContentProcessor:
    def __init__(self, layouts_dir):
        self.shortcodes = self._load_shortcodes(layouts_dir)

    def _load_shortcodes(self, layouts_dir):
        """Carrega shortcodes Python dinamicamente"""
        shortcodes = {}
        sc_dir = layouts_dir / "shortcodes"
        if not sc_dir.exists():
            return shortcodes

        for file in sc_dir.glob("*.py"):
            if file.stem == "__init__":
                continue
            try:
                spec = importlib.util.spec_from_file_location(file.stem, file)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "render"):
                    shortcodes[file.stem] = mod.render
            except Exception as e:
                print(f"⚠️  Erro ao carregar {file.stem}: {e}")
        return shortcodes

    def _parse_args(self, args):
        """Converte 'key=value key2="value"' em dict"""
        out = {}
        for match in re.finditer(r'(\w+)=(["\']?)([^"\'\s]+)\2', args):
            out[match.group(1)] = match.group(3)
        return out

    def process_shortcodes(self, content, categories=None, posts=None):
        """Processa {{< shortcode >}} no markdown"""
        if not self.shortcodes:
            return content
        
        # Early return se não há shortcodes
        if '{{<' not in content:
            return content

        categories, posts = categories or [], posts or []
        
        # Shortcodes pareados: {{< name >}}...{{< /name >}}
        paired_pattern = r'{{<\s*([^/>]+?)\s*>}}(.*?){{<\s*/\1\s*>}}'
        
        def replace_paired(match):
            tag, inner = match.groups()
            name = tag.split()[0]
            if name not in self.shortcodes:
                return match.group(0)
            args_str = tag.split(None, 1)[1] if len(tag.split()) > 1 else ""
            args = self._parse_args(args_str)
            processed_inner = self.process_shortcodes(inner, categories, posts)
            return self.shortcodes[name](categories, posts, processed_inner, **args)
        
        # Processa até não haver mais mudanças (máximo 10 iterações)
        prev, max_iterations = None, 10
        result = content
        for _ in range(max_iterations):
            result = re.sub(paired_pattern, replace_paired, result, flags=re.DOTALL)
            if result == prev:
                break
            prev = result
        
        # Shortcodes simples: {{< name >}}
        simple_pattern = r'{{<\s*([^/>]+?)\s*>}}'
        
        def replace_simple(match):
            tag = match.group(1).strip()
            parts = tag.split(None, 1)
            name = parts[0]
            if name not in self.shortcodes:
                return match.group(0)
            args_str = parts[1] if len(parts) > 1 else ""
            return self.shortcodes[name](categories, posts, "", **self._parse_args(args_str))
        
        result = re.sub(simple_pattern, replace_simple, result)
        return result

    def enhance_html(self, md_content, categories=None, posts=None):
        """Pipeline completo: shortcodes → markdown → HTML"""
        content = self.process_shortcodes(md_content, categories, posts)
        return render_gfm(content)

# ============================================================================
# GERADOR DE SITE ESTÁTICO
# ============================================================================

class StaticSiteGenerator:
    def __init__(self, output_dir=None, port=None):
        self.root = Path.cwd()
        self.content_dir = self.root / "content"
        self.layouts_dir = self.root / "layouts"
        self.output_dir = Path(output_dir or SITE_CONFIG['output_dir'])
        self.port = port or SITE_CONFIG['port']
        self.processor = ContentProcessor(self.layouts_dir)
        self.env = Environment(loader=FileSystemLoader(self.layouts_dir))
        self.env.filters['normalize'] = Utils.normalize
        self.templates = {}
        self.pages = []
        self.index_page = None
    
    def _clear_template_cache(self):
        """Limpa cache de templates (útil no live reload)"""
        self.templates.clear()
        self.env = Environment(loader=FileSystemLoader(self.layouts_dir))
        self.env.filters['normalize'] = Utils.normalize
    
    def _write(self, path, content):
        """Escreve arquivo com encoding seguro"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", errors="replace")
    
    def _template(self, name):
        """Cache de templates Jinja2"""
        if name not in self.templates:
            template_path = self.layouts_dir / name
            if not template_path.exists():
                if name == "single.html":
                    sys.exit(f"❌ Template crítico '{name}' não encontrado")
                print(f"⚠️  Template '{name}' não encontrado, usando 'single.html'")
                name = "single.html"
            self.templates[name] = self.env.get_template(name)
        return self.templates[name]
    
    def _process_file(self, filepath, is_article=True):
        """Processa arquivo Markdown individual"""
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            print(f"❌ ERRO CRÍTICO ao ler {filepath}: {e}")
            sys.exit(1)
        
        fm, md = Utils.parse_frontmatter(content)
        html = self.processor.enhance_html(md, [], self.pages)
        
        # Metadados
        title = fm.get("title", filepath.stem.replace("-", " ").title())
        series = fm.get("series", "")
        clean_title = Utils.normalize(filepath.stem)
        
        # URL de saída
        if is_article and series:
            output = f"series/{Utils.normalize(series)}/{clean_title}"
        elif is_article:
            output = f"artigos/{clean_title}"
        else:
            output = clean_title
        
        # Data
        date_str = fm.get("date", datetime.now().strftime("%Y-%m-%d"))
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            date_obj = datetime.now()
            date_str = date_obj.strftime("%Y-%m-%d")
        
        # Categorias
        category_str = fm.get("category", "Sem Categoria" if is_article else "")
        categories = [cat.strip() for cat in category_str.split(",") if cat.strip()] if is_article else []
        
        # Part (CORRIGIDO: força conversão para int)
        part = fm.get("part")
        if series:
            if part is not None:
                # Garante conversão se vier do frontmatter
                part = int(part)
            else:
                # Tenta extrair do nome do arquivo: "01-titulo.md" ou "1-titulo.md"
                if match := re.match(r'^(\d+)-', filepath.stem):
                    part = int(match.group(1))
                else:
                    part = 0
        else:
            part = 0
        
        return {
            "title": title,
            "subtitle": fm.get("subtitle", ""),
            "date": date_str,
            "timestamp": date_obj,
            "formatted_date": Utils.format_date(date_obj),
            "categories": categories,
            "category": category_str if is_article else "",
            "series": series,
            "part": part,
            "content": html,
            "output": output,
            "url": f"/{output}",
            "is_article": is_article
        }
    
    def _load_content(self):
        """Carrega todos os arquivos de conteúdo"""
        self.pages = []
        
        # Artigos e séries
        for dir_path in [self.content_dir / "articles", self.content_dir / "series"]:
            if dir_path.exists():
                for filepath in dir_path.rglob("*.md"):
                    if page := self._process_file(filepath, True):
                        self.pages.append(page)
        
        # Páginas avulsas
        for filepath in self.content_dir.glob("*.md"):
            if filepath.name != "_index.md":
                if page := self._process_file(filepath, False):
                    self.pages.append(page)
        
        # Index
        if (index_path := self.content_dir / "_index.md").exists():
            try:
                content = index_path.read_text(encoding="utf-8")
                fm, md = Utils.parse_frontmatter(content)
                self.index_page = {"title": fm.get("title", "Página Inicial"), "content": md}
            except Exception as e:
                print(f"❌ ERRO ao ler _index.md: {e}")
                sys.exit(1)
        
        self.pages.sort(key=lambda x: x["timestamp"], reverse=True)
        return self.pages, self.index_page

    def _copy_static(self):
        """Copia arquivos estáticos (images, css, js)"""
        for name in ["static", "images"]:
            src_path = self.root / name
            if not src_path.exists():
                continue
            
            dest_path = self.output_dir / name
            dest_path.mkdir(parents=True, exist_ok=True)
            
            for src_file in src_path.rglob("*"):
                if not src_file.is_file():
                    continue
                
                rel_path = src_file.relative_to(src_path)
                dest_file = dest_path / rel_path
                
                # Copia apenas se mais novo ou não existe
                if not dest_file.exists() or src_file.stat().st_mtime > dest_file.stat().st_mtime:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(src_file, dest_file)
                    except PermissionError:
                        pass

    def _render_page(self, page):
        """Renderiza uma página individual"""
        template = self._template("single.html" if page["is_article"] else "pages.html")
        html = template.render(**page)
        self._write(self.output_dir / page["output"] / "index.html", html)

    def generate(self):
        """Gera o site completo"""
        # Limpa cache de templates para recarregar mudanças
        self._clear_template_cache()
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._load_content()
        
        if not self.index_page:
            print("❌ Erro: _index.md não encontrado")
            sys.exit(1)
        
        self._copy_static()
        
        # Páginas individuais (com ou sem threading)
        if SITE_CONFIG['enable_threading']:
            with ThreadPoolExecutor() as executor:
                executor.map(self._render_page, self.pages)
        else:
            for page in self.pages:
                self._render_page(page)
        
        # Dados agregados
        articles = [p for p in self.pages if p["is_article"]]
        all_categories = sorted(set(cat for p in articles for cat in p["categories"] if cat.strip()))
        
        # Index
        html_content = self.processor.enhance_html(self.index_page["content"], all_categories, self.pages)
        artlist = self.processor.shortcodes.get("artlist", lambda *a: "")(all_categories, articles)
        self._write(
            self.output_dir / "index.html",
            self._template("index.html").render(title=self.index_page["title"], content=html_content, artlist=artlist)
        )
        
        # Páginas especiais
        pages_avulsas = [p for p in self.pages if not p["is_article"]]
        special = [
            ("artlist", "artigos", "artlist.html", "Artigos", articles),
            ("pagelist", "paginas", "pagelist.html", "Páginas", pages_avulsas),
            ("serieslist", "series", "serielist.html", "Séries", articles)
        ]
        
        for sc, out, tpl, title, data in special:
            if sc in self.processor.shortcodes:
                content = self.processor.shortcodes[sc]([], data)
                self._write(self.output_dir / out / "index.html", self._template(tpl).render(title=title, **{sc: content}))
        
        # Categorias
        if all_categories and "category" in self.processor.shortcodes:
            content = self.processor.shortcodes["category"](all_categories, articles)
            self._write(self.output_dir / "categorias" / "index.html", self._template("catlist.html").render(title="Categorias", category_list=content))
            
            if "artlist" in self.processor.shortcodes:
                for cat in all_categories:
                    cat_posts = [p for p in articles if cat in p["categories"]]
                    if cat_posts:
                        content = self.processor.shortcodes["artlist"]([cat], cat_posts)
                        self._write(
                            self.output_dir / "categorias" / Utils.normalize(cat) / "index.html",
                            self._template("categoria.html").render(title=cat, category_normalized=Utils.normalize(cat), artlist=content)
                        )
        
        # Séries
        series_list = sorted(set(p["series"] for p in articles if p["series"]))
        if series_list and "artlist" in self.processor.shortcodes:
            for serie in series_list:
                posts = sorted([p for p in articles if p["series"] == serie], key=lambda x: (x.get("part", 0), x["timestamp"]))
                if posts:
                    content = self.processor.shortcodes["artlist"]([], posts)
                    self._write(
                        self.output_dir / "series" / Utils.normalize(serie) / "index.html",
                        self._template("serie.html").render(title=serie, series_normalized=Utils.normalize(serie), artlist=content)
                    )
        
        # 404
        self._write(self.output_dir / "404.html", self._template("404.html").render())
        print(f"✅ Site gerado em: {self.output_dir}")

    def serve(self):
        """Servidor local com live reload"""
        class Handler(FileSystemEventHandler):
            def __init__(self, gen):
                self.gen = gen
                self.last_modified = 0
            
            def on_modified(self, event):
                if event.is_directory:
                    return
                
                # Debouncing: ignora eventos muito próximos
                now = time.time()
                if now - self.last_modified < SITE_CONFIG['debounce_delay']:
                    return
                
                self.last_modified = now
                print(f"📝 Modificado: {event.src_path}")
                try:
                    self.gen.generate()
                except Exception as e:
                    print(f"⚠️  Erro ao regenerar: {e}")
        
        os.chdir(self.output_dir)
        httpd = socketserver.TCPServer(("", self.port), http.server.SimpleHTTPRequestHandler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print(f"🌐 Servidor: http://localhost:{self.port}")
        
        observer = Observer()
        for path in [self.content_dir, self.layouts_dir, self.root/"static", self.root/"images"]:
            if path.exists():
                observer.schedule(Handler(self), path, recursive=True)
        
        observer.start()
        print("👀 Monitorando mudanças...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            httpd.shutdown()
        observer.join()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gerador de site estático")
    parser.add_argument('--serve', action='store_true', help='Servidor com live reload')
    parser.add_argument('--port', type=int, default=SITE_CONFIG['port'], help=f"Porta (padrão: {SITE_CONFIG['port']})")
    parser.add_argument('--threading', action='store_true', help='Ativa paralelização (útil para +100 páginas)')
    args = parser.parse_args()
    
    if args.threading:
        SITE_CONFIG['enable_threading'] = True
    
    gen = StaticSiteGenerator("public", args.port)
    gen.generate()
    if args.serve:
        gen.serve()

if __name__ == "__main__":
    main()