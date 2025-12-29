import sys, shutil, re, os, time, threading, unicodedata, importlib.util
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
import markdown, http.server, socketserver
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ============================================================================
# UTILIDADES
# ============================================================================

class Utils:
    MONTHS = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    VIDEO_EXTS = ('.mp4', '.webm', '.ogg', '.avi', '.mov', '.wmv', '.flv', '.mkv')
    
    @staticmethod
    def normalize(text):
        """Normaliza texto para URL-safe"""
        normalized = unicodedata.normalize('NFKD', text)
        ascii_text = ''.join(c for c in normalized if not unicodedata.combining(c))
        return re.sub(r'-{2,}', '-', re.sub(r'[<>:"/\\|?*%\s]+', '-', ascii_text.lower())).strip('-')
    
    @staticmethod
    def safe_remove_tree(path, max_retries=3):
        """Remove diretório com retry"""
        for attempt in range(max_retries):
            try:
                if path.exists():
                    shutil.rmtree(path)
                return True
            except PermissionError:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
        return False
    
    @staticmethod
    def parse_frontmatter(content):
        """Extrai frontmatter YAML"""
        lines = content.strip().splitlines()
        if not lines or lines[0] != "---":
            return {"title": "Sem Título", "date": datetime.now().strftime("%Y-%m-%d")}, content
        
        front_matter, content_start = {}, 0
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                content_start = i + 1
                break
            if ":" in line:
                key, value = map(str.strip, line.split(":", 1))
                front_matter[key] = value
        
        return front_matter, "\n".join(lines[content_start:]).strip()
    
    @classmethod
    def format_date(cls, date_str):
        """Formata data para exibição"""
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            return f"{date.day:02d} - {cls.MONTHS[date.month - 1]} - {date.year}"
        except ValueError:
            return datetime.now().strftime("%d - %b - %Y")

# ============================================================================
# PROCESSADOR DE CONTEÚDO
# ============================================================================

class ContentProcessor:
    def __init__(self, layouts_dir):
        self.shortcodes = self._load_shortcodes(layouts_dir)
        self.md = markdown.Markdown(
            extensions=['meta', 'extra', 'codehilite', 'toc', 'nl2br', 'sane_lists'],
            extension_configs={'codehilite': {'use_pygments': False, 'css_class': 'highlight'}}
        )
    
    def _load_shortcodes(self, layouts_dir):
        """Carrega shortcodes dinamicamente"""
        shortcodes = {}
        shortcodes_dir = layouts_dir / "shortcodes"
        if not shortcodes_dir.exists():
            return shortcodes
        
        for filepath in shortcodes_dir.glob("*.py"):
            if filepath.stem == "__init__":
                continue
            try:
                spec = importlib.util.spec_from_file_location(filepath.stem, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, "render"):
                        shortcodes[filepath.stem] = module.render
            except Exception:
                continue
        
        return shortcodes
    
    def _parse_args(self, args):
        """Parse argumentos de shortcode"""
        kwargs = {}
        for arg in args.split():
            if '=' in arg:
                key, value = arg.split('=', 1)
                kwargs[key.strip()] = value.strip().strip('"\'')
        return kwargs
    
    def process_shortcodes(self, content, categories=None, posts=None):
        """Processa shortcodes (paired e simple)"""
        if not self.shortcodes:
            return content
        
        categories, posts, result = categories or [], posts or [], content
        
        # Shortcodes pareados
        paired_pattern = r'{{<\s*([^/>]+?)\s*>}}(.*?){{<\s*/([^>]+?)\s*>}}'
        for _ in range(5):
            if not re.search(paired_pattern, result, re.DOTALL):
                break
            
            def replace_paired(m):
                opening, inner, closing = m.groups()
                name = opening.split()[0]
                if name != closing or name not in self.shortcodes:
                    return ""
                args = self._parse_args(opening.split(None, 1)[1] if len(opening.split()) > 1 else "")
                try:
                    return self.shortcodes[name](categories, posts, self.process_shortcodes(inner, categories, posts), **args)
                except:
                    return ""
            
            result = re.sub(paired_pattern, replace_paired, result, flags=re.DOTALL)
        
        # Shortcodes simples
        simple_pattern = r'{{<\s*([^/>]+?)\s*>}}'
        for _ in range(5):
            if not re.search(simple_pattern, result):
                break
            
            def replace_simple(m):
                tag = m.group(1).strip()
                if tag.startswith('/'):
                    return ""
                parts = tag.split(None, 1)
                name, args = parts[0], parts[1] if len(parts) > 1 else ""
                if name in self.shortcodes:
                    try:
                        return self.shortcodes[name](categories, posts, "", **self._parse_args(args))
                    except:
                        pass
                return ""
            
            result = re.sub(simple_pattern, replace_simple, result)
        
        return result
    
    def _process_media(self, soup):
        """Processa imagens e vídeos"""
        for img in soup.find_all("img"):
            if img.get("data-shortcode"):
                continue
            
            src = img.get("src", "")
            
            # Vídeos
            if any(src.lower().endswith(ext) for ext in Utils.VIDEO_EXTS):
                video_src = src.replace("../", "/") if src.startswith("../") else \
                           f"/videos/{src}" if not src.startswith(("/", "http")) else src
                
                video = soup.new_tag("video", controls=True, **{"class": "video-player"})
                source = soup.new_tag("source", src=video_src, type=f"video/{Path(src).suffix[1:]}")
                video.append(source)
                
                figure = soup.new_tag("figure", **{"class": "video-figure"})
                figure.append(video)
                
                if (alt := img.get("alt")) and not re.match(r'^https?://', alt):
                    figcaption = soup.new_tag("figcaption")
                    figcaption.string = alt
                    figure.append(figcaption)
                
                img.replace_with(figure)
            
            # Imagens
            else:
                figure = soup.new_tag("figure", **{"class": "image-figure"})
                img.wrap(figure)
                
                if (alt := img.get("alt")) and not re.match(r'^https?://', alt):
                    figcaption = soup.new_tag("figcaption")
                    figcaption.string = alt
                    figure.append(figcaption)
                
                if src.startswith("../"):
                    img["src"] = src.replace("../", "/")
                elif not src.startswith(("/", "http")):
                    img["src"] = f"/images/{src}"
    
    def _generate_toc(self, soup):
        """Gera índice de conteúdo"""
        toc, counters, used_ids = [], [0, 0, 0, 0], set()
        has_h1 = any(h.name == "h1" for h in soup.find_all(['h1', 'h2', 'h3', 'h4']))
        
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            level = int(heading.name[1]) - 1
            
            # Reset counters
            for i in range(level + 1, 4):
                counters[i] = 0
            counters[level] += 1
            
            # ID único
            base_id = Utils.normalize(heading.get_text().strip())
            heading_id, counter = base_id, 1
            while heading_id in used_ids:
                heading_id = f"{base_id}-{counter}"
                counter += 1
            used_ids.add(heading_id)
            heading['id'] = heading_id
            
            # Numeração
            if level == 0:
                number = f"{counters[0]}."
            elif level == 1:
                number = f"{counters[0]}.{counters[1]}." if has_h1 else f"{counters[1]}."
            elif level == 2:
                number = f"{counters[0]}.{counters[1]}.{counters[2]}." if has_h1 else f"{counters[1]}.{counters[2]}."
            else:
                number = f"{counters[0]}.{counters[1]}.{counters[2]}.{counters[3]}." if has_h1 else f"{counters[1]}.{counters[2]}.{counters[3]}."
            
            toc.append({
                "level": heading.name,
                "text": heading.get_text().strip(),
                "id": heading_id,
                "number": number,
                "indent": level
            })
        
        return soup, toc
    
    def enhance_html(self, md_content, categories=None, posts=None):
        """Processa markdown e gera HTML aprimorado"""
        content = self.process_shortcodes(md_content, categories, posts)
        html = self.md.convert(content)
        soup = BeautifulSoup(html, "html.parser")
        
        self._process_media(soup)
        soup, toc = self._generate_toc(soup)
        
        return str(soup), toc

# ============================================================================
# GERADOR DE SITE ESTÁTICO
# ============================================================================

class StaticSiteGenerator:
    def __init__(self, output_dir="public", port=8000):
        self.root = Path.cwd()
        self.content_dir = self.root / "content"
        self.layouts_dir = self.root / "layouts"
        self.output_dir = Path(output_dir)
        self.port = port
        
        self.processor = ContentProcessor(self.layouts_dir)
        self.env = Environment(loader=FileSystemLoader(self.layouts_dir))
        self.env.filters['normalize'] = Utils.normalize
        
        self.templates = {}
        self.pages = []
        self.index_page = None
    
    def _write(self, path, content):
        """Escreve arquivo com encoding UTF-8"""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", errors="replace")
    
    def _template(self, name):
        """Cache de templates"""
        if name not in self.templates:
            if not (self.layouts_dir / name).exists():
                name = "single.html" if name != "single.html" else sys.exit(f"Template {name} não encontrado")
            self.templates[name] = self.env.get_template(name)
        return self.templates[name]
    
    def _process_file(self, filepath, is_article=True):
        """Processa arquivo markdown"""
        try:
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except:
            return {}
        
        front_matter, md_content = Utils.parse_frontmatter(content)
        html_content, toc = self.processor.enhance_html(md_content, [], self.pages)
        
        # Metadata
        title = front_matter.get("title", filepath.stem.replace("-", " ").title())
        series = front_matter.get("series", "")
        clean_title = Utils.normalize(filepath.stem)
        
        # Output path
        output = f"series/{Utils.normalize(series)}/{clean_title}" if is_article and series else \
                f"artigos/{clean_title}" if is_article else clean_title
        
        # Data
        date_str = front_matter.get("date", datetime.now().strftime("%Y-%m-%d"))
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Categorias
        category_str = front_matter.get("category", "Sem Categoria" if is_article else "")
        categories = [cat.strip() for cat in category_str.split(",") if cat.strip()] if is_article else []
        
        # Part (para séries)
        part = front_matter.get("part")
        if part is None and series:
            if match := re.match(r'(\d+)-.*', filepath.stem):
                part = int(match.group(1))
            elif match := re.match(r'(\d+)\s*[-:]\s*(.*)', title):
                part = int(match.group(1))
                title = match.group(2).strip()
            else:
                part = 0
        
        return {
            "title": title,
            "date": date_str,
            "formatted_date": Utils.format_date(date_str),
            "categories": categories,
            "category": category_str if is_article else "",
            "series": series,
            "part": int(part) if part is not None else 0,
            "content": html_content,
            "output": output,
            "url": f"/{output}",
            "is_article": is_article,
            "toc": toc
        }
    
    def _load_content(self):
        """Carrega todo o conteúdo"""
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
                content = index_path.read_text(encoding="utf-8", errors="replace")
                front_matter, md_content = Utils.parse_frontmatter(content)
                self.index_page = {
                    "title": front_matter.get("title", "Página Inicial"),
                    "content": md_content
                }
            except:
                pass
        
        self.pages.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"), reverse=True)
        return self.pages, self.index_page
    
    def _get_navigation(self, pages, index):
        """Calcula navegação prev/next"""
        current = pages[index]
        series = current.get("series", "")
        
        # Filtrar páginas navegáveis
        if current["is_article"]:
            nav_pages = sorted(
                [p for p in pages if p["is_article"] and (p["series"] == series if series else not p["series"])],
                key=lambda x: (x.get("part", 0), datetime.strptime(x["date"], "%Y-%m-%d"))
            )
        else:
            nav_pages = sorted(
                [p for p in pages if not p["is_article"]],
                key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d")
            )
        
        nav_index = next((i for i, p in enumerate(nav_pages) if p["url"] == current["url"]), -1)
        if nav_index == -1:
            return None, None
        
        prev = nav_pages[nav_index - 1] if nav_index > 0 else None
        next_ = nav_pages[nav_index + 1] if nav_index < len(nav_pages) - 1 else None
        
        return prev, next_
    
    def _copy_static(self):
        """Copia arquivos estáticos"""
        for src_name, dest_name in [("static", "static"), ("images", "images"), ("videos", "videos")]:
            if not (src_path := self.root / src_name).exists():
                continue
            
            dest_path = self.output_dir / dest_name
            dest_path.mkdir(parents=True, exist_ok=True)
            
            for src_file in src_path.rglob("*"):
                if not src_file.is_file():
                    continue
                
                rel_path = src_file.relative_to(src_path)
                dest_file = dest_path / rel_path
                
                # Copiar apenas se necessário
                if not dest_file.exists() or src_file.stat().st_mtime > dest_file.stat().st_mtime:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(src_file, dest_file)
                    except PermissionError:
                        pass
    
    def generate(self):
        """Gera o site completo"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._load_content()
        
        if not self.index_page:
            return print("Erro: _index.md não encontrado")
        
        self._copy_static()
        
        # Páginas individuais
        for i, page in enumerate(self.pages):
            template = self._template("single.html" if page["is_article"] else "pages.html")
            nav_pages = [p for p in self.pages if p["is_article"]] if page["is_article"] else self.pages
            nav_index = next((j for j, p in enumerate(nav_pages) if p["url"] == page["url"]), i)
            prev, next_ = self._get_navigation(nav_pages, nav_index)
            
            html = template.render(
                title=page["title"],
                content=page["content"],
                formatted_date=page["formatted_date"],
                category=page["category"],
                series=page["series"],
                previous=prev or {},
                next=next_ or {},
                toc=page["toc"],
                url=page["url"]
            )
            
            self._write(self.output_dir / page["output"] / "index.html", html)
        
        # Index
        template = self._template("index.html")
        articles = [p for p in self.pages if p["is_article"]]
        categories = sorted(set(cat for p in articles for cat in p["categories"] if cat.strip()))
        
        content = self.processor.process_shortcodes(self.index_page["content"], categories, self.pages)
        html_content, _ = self.processor.enhance_html(content, categories, self.pages)
        artlist = self.processor.shortcodes.get("artlist", lambda *args: "")(categories, articles)
        
        html = template.render(title=self.index_page["title"], content=html_content, artlist=artlist)
        self._write(self.output_dir / "index.html", html)
        
        # Páginas especiais
        pages = [p for p in self.pages if not p["is_article"]]
        
        special_pages = [
            ("artlist", "artigos", "artlist.html", "Artigos", articles),
            ("pagelist", "paginas", "pagelist.html", "Páginas Avulsas", pages),
            ("serieslist", "series", "serielist.html", "Séries", articles)
        ]
        
        for shortcode, output, template_name, title, data in special_pages:
            if shortcode in self.processor.shortcodes:
                content = self.processor.shortcodes[shortcode]([], data)
                html = self._template(template_name).render(title=title, **{shortcode: content})
                self._write(self.output_dir / output / "index.html", html)
        
        # Categorias
        if categories and "category" in self.processor.shortcodes:
            content = self.processor.shortcodes["category"](categories, articles)
            self._write(
                self.output_dir / "categorias" / "index.html",
                self._template("catlist.html").render(title="Categorias", category_list=content)
            )
            
            if "artlist" in self.processor.shortcodes:
                for category in categories:
                    cat_posts = [p for p in articles if category in p["categories"]]
                    if cat_posts:
                        content = self.processor.shortcodes["artlist"]([category], cat_posts)
                        self._write(
                            self.output_dir / "categorias" / Utils.normalize(category) / "index.html",
                            self._template("categoria.html").render(
                                title=category,
                                category_normalized=Utils.normalize(category),
                                artlist=content
                            )
                        )
        
        # Séries
        series_list = sorted(set(p["series"] for p in articles if p["series"]))
        if series_list and "artlist" in self.processor.shortcodes:
            for serie in series_list:
                series_posts = sorted(
                    [p for p in articles if p["series"] == serie],
                    key=lambda x: (x.get("part", 0), datetime.strptime(x["date"], "%Y-%m-%d"))
                )
                if series_posts:
                    content = self.processor.shortcodes["artlist"]([], series_posts)
                    self._write(
                        self.output_dir / "series" / Utils.normalize(serie) / "index.html",
                        self._template("serie.html").render(
                            title=serie,
                            series_normalized=Utils.normalize(serie),
                            artlist=content
                        )
                    )
        
        # 404
        self._write(self.output_dir / "404.html", self._template("404.html").render())
        
        print(f"Site gerado em: {self.output_dir}")
    
    def serve(self):
        """Servidor com live reload"""
        class Handler(FileSystemEventHandler):
            def __init__(self, gen):
                self.gen = gen
            
            def on_modified(self, event):
                if not event.is_directory:
                    print(f"Modificado: {event.src_path}")
                    self.gen.generate()
        
        os.chdir(self.output_dir)
        httpd = socketserver.TCPServer(("", self.port), http.server.SimpleHTTPRequestHandler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        print(f"Servidor: http://localhost:{self.port}")
        
        observer = Observer()
        handler = Handler(self)
        
        watch_paths = [
            self.content_dir,
            self.layouts_dir,
            self.root / "static",
            self.root / "images",
            self.root / "videos"
        ]
        
        for path in watch_paths:
            if path.exists():
                observer.schedule(handler, path, recursive=True)
        
        observer.start()
        print("Monitorando mudanças...")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            httpd.shutdown()
        
        observer.join()

# ============================================================================
# MAIN
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerador de site estático")
    parser.add_argument('--serve', action='store_true', help='Servidor com live reload')
    parser.add_argument('--port', type=int, default=8000, help='Porta (padrão: 8000)')
    args = parser.parse_args()
    
    gen = StaticSiteGenerator("public", args.port)
    gen.generate()
    
    if args.serve:
        gen.serve()

if __name__ == "__main__":
    main()