import sys, shutil, re, os, time, threading, unicodedata, importlib.util, subprocess
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup
import http.server, socketserver
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

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
        return re.sub(r'-{2,}', '-', re.sub(r'[<>:"/\\|?*%\s]+', '-', ascii_text.lower())).strip('-')

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
# GFM RENDERER (CommonMark REAL)
# ============================================================================

def render_gfm(markdown_text: str) -> str:
    process = subprocess.Popen(
        ["node", "gfm.js"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    html, err = process.communicate(markdown_text)
    if process.returncode != 0:
        raise RuntimeError(err)
    return html


# ============================================================================
# PROCESSADOR DE CONTEÚDO
# ============================================================================

class ContentProcessor:
    def __init__(self, layouts_dir):
        self.shortcodes = self._load_shortcodes(layouts_dir)

    def _load_shortcodes(self, layouts_dir):
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
            except Exception:
                pass
        return shortcodes

    def _parse_args(self, args):
        out = {}
        for arg in args.split():
            if '=' in arg:
                k, v = arg.split("=", 1)
                out[k.strip()] = v.strip().strip('"\'')
        return out

    def process_shortcodes(self, content, categories=None, posts=None):
        if not self.shortcodes:
            return content

        categories, posts = categories or [], posts or []
        result = content

        # Shortcodes pareados (com conteúdo interno)
        paired = r'{{<\s*([^/>]+?)\s*>}}(.*?){{<\s*/([^>]+?)\s*>}}'
        for _ in range(5):
            if not re.search(paired, result, re.DOTALL):
                break

            def repl(m):
                open_, inner, close = m.groups()
                name = open_.split()[0]
                if name != close or name not in self.shortcodes:
                    return ""
                args = self._parse_args(open_.split(None, 1)[1] if len(open_.split()) > 1 else "")
                return self.shortcodes[name](categories, posts, self.process_shortcodes(inner, categories, posts), **args)

            result = re.sub(paired, repl, result, flags=re.DOTALL)

        # Shortcodes simples (sem conteúdo interno)
        simple = r'{{<\s*([^/>]+?)\s*>}}'
        for _ in range(5):
            if not re.search(simple, result):
                break

            def repl(m):
                tag = m.group(1).strip()
                parts = tag.split(None, 1)
                name, args = parts[0], parts[1] if len(parts) > 1 else ""
                if name in self.shortcodes:
                    return self.shortcodes[name](categories, posts, "", **self._parse_args(args))
                return ""

            result = re.sub(simple, repl, result)

        return result

    def _process_media(self, soup):
        """Processa imagens adicionando figure e figcaption"""
        for img in soup.find_all("img"):
            # Pula se já estiver dentro de um figure
            if img.parent.name == 'figure':
                continue
                
            # Envolve a imagem em <figure>
            fig = soup.new_tag("figure")
            img.wrap(fig)
            
            # Se houver alt text, adiciona como <figcaption>
            alt_text = img.get("alt", "").strip()
            if alt_text:
                caption = soup.new_tag("figcaption")
                caption.string = alt_text
                fig.append(caption)

    def _generate_toc(self, soup):
        toc, used = [], set()
        counters = [0, 0, 0]  # [h2, h3, h4]

        for h in soup.find_all(['h2','h3','h4']):
            hid = Utils.normalize(h.get_text())
            if hid in used:
                hid += "-1"
            used.add(hid)
            h['id'] = hid

            level = int(h.name[1]) - 2  # h2 -> 0, h3 -> 1, h4 -> 2

            counters[level] += 1
            for i in range(level + 1, len(counters)):
                counters[i] = 0

            number = ".".join(str(counters[i]) for i in range(level + 1) if counters[i] > 0) + "."

            toc.append({
                "level": h.name,
                "text": h.get_text(),
                "id": hid,
                "indent": level,
                "number": number
            })

        return soup, toc

    def enhance_html(self, md_content, categories=None, posts=None):
        """Processa shortcodes e converte markdown para HTML"""
        # Primeiro: processa shortcodes no markdown
        content = self.process_shortcodes(md_content, categories, posts)
        
        # Segundo: converte markdown para HTML
        html = render_gfm(content)
        
        # Terceiro: processa o HTML com BeautifulSoup
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
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", errors="replace")
    
    def _template(self, name):
        if name not in self.templates:
            if not (self.layouts_dir / name).exists():
                if name != "single.html": 
                    name = "single.html"
                else: 
                    sys.exit(f"Template {name} não encontrado")
            self.templates[name] = self.env.get_template(name)
        return self.templates[name]
    
    def _process_file(self, filepath, is_article=True):
        try: 
            content = filepath.read_text(encoding="utf-8", errors="replace")
        except: 
            return {}
        
        front_matter, md_content = Utils.parse_frontmatter(content)
        html_content, toc = self.processor.enhance_html(md_content, [], self.pages)
        
        title = front_matter.get("title", filepath.stem.replace("-", " ").title())
        series = front_matter.get("series", "")
        clean_title = Utils.normalize(filepath.stem)
        
        output = f"series/{Utils.normalize(series)}/{clean_title}" if is_article and series else \
                 f"artigos/{clean_title}" if is_article else clean_title
        
        date_str = front_matter.get("date", datetime.now().strftime("%Y-%m-%d"))
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            date_obj = datetime.now()
            date_str = date_obj.strftime("%Y-%m-%d")
            
        category_str = front_matter.get("category", "Sem Categoria" if is_article else "")
        categories = [cat.strip() for cat in category_str.split(",") if cat.strip()] if is_article else []
        
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
            "subtitle": front_matter.get("subtitle", ""),
            "date": date_str,
            "timestamp": date_obj,
            "formatted_date": Utils.format_date(date_obj),
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
        self.pages = []
        for dir_path in [self.content_dir / "articles", self.content_dir / "series"]:
            if dir_path.exists():
                for filepath in dir_path.rglob("*.md"):
                    if page := self._process_file(filepath, True): 
                        self.pages.append(page)
        
        for filepath in self.content_dir.glob("*.md"):
            if filepath.name != "_index.md":
                if page := self._process_file(filepath, False): 
                    self.pages.append(page)
        
        if (index_path := self.content_dir / "_index.md").exists():
            try:
                content = index_path.read_text(encoding="utf-8", errors="replace")
                fm, md = Utils.parse_frontmatter(content)
                self.index_page = {"title": fm.get("title", "Página Inicial"), "content": md}
            except: 
                pass
        
        self.pages.sort(key=lambda x: x["timestamp"], reverse=True)
        return self.pages, self.index_page

    def _copy_static(self):
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
                if not dest_file.exists() or src_file.stat().st_mtime > dest_file.stat().st_mtime:
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    try: 
                        shutil.copy2(src_file, dest_file)
                    except PermissionError: 
                        pass

    def _clean_output_dir(self):
        """Limpa o diretório public/ preservando apenas .git"""
        if not self.output_dir.exists():
            return
        
        git_dir = self.output_dir / ".git"
        
        # Deleta TUDO exceto .git
        def remove_readonly(func, path, _):
            os.chmod(path, 0o777)
            func(path)
        
        for item in self.output_dir.iterdir():
            if item.name == ".git":
                continue
            
            try:
                if item.is_dir():
                    shutil.rmtree(item, onerror=remove_readonly)
                else:
                    item.unlink()
            except Exception as e:
                print(f"Aviso: Não foi possível deletar {item}: {e}")

    def generate(self):
        # LIMPA TUDO ANTES DE GERAR (exceto .git)
        self._clean_output_dir()
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._load_content()
        if not self.index_page: 
            return print("Erro: _index.md não encontrado")
        self._copy_static()
        
        # Páginas Individuais
        for page in self.pages:
            template = self._template("single.html" if page["is_article"] else "pages.html")
            
            html = template.render(
                title=page["title"],
                subtitle=page["subtitle"],
                content=page["content"],
                formatted_date=page["formatted_date"],
                categories=page["categories"],
                category=page["category"],
                series=page["series"],
                toc=page["toc"],
                url=page["url"]
            )
            self._write(self.output_dir / page["output"] / "index.html", html)
        
        # Preparação de dados
        articles = [p for p in self.pages if p["is_article"]]
        all_categories = sorted(set(cat for p in articles for cat in p["categories"] if cat.strip()))
        
        # Index - CORRIGIDO: só chama enhance_html uma vez
        template = self._template("index.html")
        html_content, _ = self.processor.enhance_html(self.index_page["content"], all_categories, self.pages)
        artlist = self.processor.shortcodes.get("artlist", lambda *args: "")(all_categories, articles)
        
        self._write(self.output_dir / "index.html", template.render(
            title=self.index_page["title"], 
            content=html_content, 
            artlist=artlist
        ))
        
        # Páginas Especiais
        pages_avulsas = [p for p in self.pages if not p["is_article"]]
        special_pages = [
            ("artlist", "artigos", "artlist.html", "Artigos", articles),
            ("pagelist", "paginas", "pagelist.html", "Páginas Avulsas", pages_avulsas),
            ("serieslist", "series", "serielist.html", "Séries", articles)
        ]
        
        for shortcode, output, tpl, title, data in special_pages:
            if shortcode in self.processor.shortcodes:
                content = self.processor.shortcodes[shortcode]([], data)
                self._write(
                    self.output_dir / output / "index.html", 
                    self._template(tpl).render(title=title, **{shortcode: content})
                )
        
        # Categorias
        if all_categories and "category" in self.processor.shortcodes:
            content = self.processor.shortcodes["category"](all_categories, articles)
            self._write(
                self.output_dir / "categorias" / "index.html", 
                self._template("catlist.html").render(title="Categorias", category_list=content)
            )
            
            if "artlist" in self.processor.shortcodes:
                for category in all_categories:
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
                    key=lambda x: (x.get("part", 0), x["timestamp"])
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
        for path in [self.content_dir, self.layouts_dir, self.root/"static", self.root/"images"]:
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