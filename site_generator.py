"""Quantum Brief - 静的サイト生成エンジン

articles/ ディレクトリ内のJSON記事データを読み込み、
Jinja2テンプレートを使って静的HTMLサイトを生成する。
"""

import json
import math
import shutil
import re
from datetime import datetime
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

from config import (
    BLOG_NAME,
    BLOG_DESCRIPTION,
    BLOG_URL,
    ARTICLES_DIR,
    SITE_DIR,
    BLOG_LANGUAGE,
)


class SiteGenerator:
    """静的サイト生成クラス"""

    # 1ページあたりの記事数（ページネーション用）
    ARTICLES_PER_PAGE = 50

    def __init__(self):
        """Jinja2テンプレート環境と出力ディレクトリの初期化"""
        template_dir = Path(__file__).parent / "templates"

        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True,
        )

        self.output_dir = SITE_DIR

        self.md = markdown.Markdown(
            extensions=["toc", "fenced_code", "tables", "meta"],
            extension_configs={
                "toc": {"title": "目次", "toc_depth": "2-3"},
            },
        )

    # ------------------------------------------------------------------
    # メインビルド
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_slug(slug):
        """記事のファイル名は日本語を含む単一componentだけを許可する。"""
        if (not isinstance(slug, str) or not slug or slug in {".", ".."}
                or slug[-1] in ". " or any(ord(c) < 32 for c in slug)
                or any(c in slug for c in '/\\:<>"|?*')
                or re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", slug.split(".")[0], re.I)):
            raise ValueError("Invalid article slug")
        # 配備先の255-byte componentとWindowsの255 UTF-16 unitsの両方に収める。
        filename = slug + ".html"
        try:
            too_long = len(filename.encode("utf-8")) > 255 or len(filename.encode("utf-16-le")) > 510
        except UnicodeError:
            raise ValueError("Invalid article slug encoding") from None
        if too_long:
            raise ValueError("Article filename is too long")
        return slug

    def _article_output_path(self, slug):
        slug = self._validate_slug(slug)
        root = Path(self.output_dir).absolute()
        directory = root / "articles"
        target = directory / (slug + ".html")
        for candidate in (root, directory, target):
            if candidate.exists() or candidate.is_symlink():
                stat = candidate.lstat()
                if candidate.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                    raise ValueError("Linked article output is not allowed")
                if candidate == target and (not candidate.is_file() or stat.st_nlink != 1):
                    raise ValueError("Invalid article output")
        if directory.resolve().parent != root.resolve() or target.resolve().parent != directory.resolve():
            raise ValueError("Article output escapes its directory")
        return target


    def build_site(self):
        """全記事を読み込んで静的サイトを一括生成する"""
        print(f"[サイト生成] 開始 - 出力先: {self.output_dir}")

        # Validate every slug and existing output link before clearing the old build.
        articles = self._load_articles()
        names = set()
        for article in articles:
            slug = article.get("slug", article.get("id", "untitled"))
            self._article_output_path(slug)
            key = slug.casefold()
            if key in names:
                raise ValueError("Duplicate article slug")
            names.add(key)

        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        (self.output_dir / "articles").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "category").mkdir(parents=True, exist_ok=True)

        # ---- 記事の読み込み ----
        if not articles:
            print("[サイト生成] 記事が見つかりません。空のサイトを生成します。")

        articles.sort(key=lambda a: a.get("date", ""), reverse=True)

        print(f"[サイト生成] 記事数: {len(articles)}")

        # ---- 各記事ページの生成 ----
        for article in articles:
            html = self._render_article(article)
            slug = article.get("slug", article.get("id", "untitled"))
            output_path = self._article_output_path(slug)
            with output_path.open("x", encoding="utf-8") as output:
                output.write(html)
            print(f"  記事生成: {slug}.html")

        # ---- インデックスページの生成（ページネーション対応） ----
        total_pages = max(1, math.ceil(len(articles) / self.ARTICLES_PER_PAGE))
        for page_num in range(1, total_pages + 1):
            start = (page_num - 1) * self.ARTICLES_PER_PAGE
            end = start + self.ARTICLES_PER_PAGE
            page_articles = articles[start:end]

            html = self._render_index(
                page_articles,
                articles=articles,
                current_page=page_num,
                total_pages=total_pages,
            )
            if page_num == 1:
                (self.output_dir / "index.html").write_text(html, encoding="utf-8")
            else:
                page_dir = self.output_dir / "page"
                page_dir.mkdir(parents=True, exist_ok=True)
                (page_dir / f"{page_num}.html").write_text(html, encoding="utf-8")

        print(f"  インデックス生成: {total_pages} ページ")

        # ---- カテゴリページの生成 ----
        categories = self._group_by_category(articles)
        for category, cat_articles in categories.items():
            html = self._render_category(category, cat_articles)
            safe_name = self._slugify(category)
            output_path = self.output_dir / "category" / f"{safe_name}.html"
            output_path.write_text(html, encoding="utf-8")
            print(f"  カテゴリ生成: {category} ({len(cat_articles)} 記事)")

        # ---- サイトマップ生成 ----
        self._generate_sitemap(articles)
        print("  サイトマップ生成: sitemap.xml")

        # ---- RSSフィード生成 ----
        self._generate_rss(articles)
        print("  RSSフィード生成: feed.xml")

        print(f"[サイト生成] 完了 - {self.output_dir}")

    # ------------------------------------------------------------------
    # 記事読み込み
    # ------------------------------------------------------------------

    def _load_articles(self) -> list:
        """articles/ ディレクトリからJSON記事ファイルを読み込む"""
        articles = []
        if not ARTICLES_DIR.exists():
            return articles

        for filepath in sorted(ARTICLES_DIR.glob("*.json")):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    article = json.load(f)

                article.setdefault("title", "無題")
                article.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
                article.setdefault("category", "未分類")
                article.setdefault("tags", [])
                article.setdefault("content", "")
                article.setdefault("description", "")
                article.setdefault("slug", filepath.stem)

                articles.append(article)
            except (json.JSONDecodeError, IOError) as e:
                print(f"  [警告] 記事読み込みエラー: {filepath} - {e}")

        return articles

    # ------------------------------------------------------------------
    # レンダリング
    # ------------------------------------------------------------------

    def _render_article(self, article: dict) -> str:
        """記事HTMLをレンダリングして返す"""
        self.md.reset()
        html_content = self.md.convert(article.get("content", ""))
        toc = getattr(self.md, "toc", "")
        related = article.get("related", [])

        template = self.env.get_template("article.html")
        return template.render(
            blog_name=BLOG_NAME,
            blog_description=BLOG_DESCRIPTION,
            blog_url=BLOG_URL,
            blog_language=BLOG_LANGUAGE,
            article=article,
            content=html_content,
            toc=toc,
            related=related,
        )

    def _render_index(
        self,
        page_articles: list,
        articles: list = None,
        current_page: int = 1,
        total_pages: int = 1,
    ) -> str:
        """トップページ（記事一覧）をレンダリングして返す"""
        if articles is None:
            articles = page_articles

        categories = self._group_by_category(articles)

        template = self.env.get_template("index.html")
        return template.render(
            blog_name=BLOG_NAME,
            blog_description=BLOG_DESCRIPTION,
            blog_url=BLOG_URL,
            blog_language=BLOG_LANGUAGE,
            articles=page_articles,
            categories=categories,
            current_page=current_page,
            total_pages=total_pages,
        )

    def _render_category(self, category: str, articles: list) -> str:
        """カテゴリページをレンダリングして返す"""
        template = self.env.get_template("category.html")
        return template.render(
            blog_name=BLOG_NAME,
            blog_description=BLOG_DESCRIPTION,
            blog_url=BLOG_URL,
            blog_language=BLOG_LANGUAGE,
            category=category,
            articles=articles,
            article_count=len(articles),
        )

    # ------------------------------------------------------------------
    # XML生成
    # ------------------------------------------------------------------

    def _generate_sitemap(self, articles: list):
        """サイトマップ(sitemap.xml)を生成する"""
        urls = []

        urls.append(
            {
                "loc": BLOG_URL,
                "lastmod": datetime.now().strftime("%Y-%m-%d"),
                "changefreq": "daily",
                "priority": "1.0",
            }
        )

        for article in articles:
            slug = article.get("slug", "untitled")
            urls.append(
                {
                    "loc": f"{BLOG_URL}/articles/{slug}.html",
                    "lastmod": article.get("date", datetime.now().strftime("%Y-%m-%d")),
                    "changefreq": "monthly",
                    "priority": "0.8",
                }
            )

        categories = self._group_by_category(articles)
        for category in categories:
            safe_name = self._slugify(category)
            urls.append(
                {
                    "loc": f"{BLOG_URL}/category/{safe_name}.html",
                    "lastmod": datetime.now().strftime("%Y-%m-%d"),
                    "changefreq": "weekly",
                    "priority": "0.6",
                }
            )

        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append(
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        )
        for url in urls:
            xml_lines.append("  <url>")
            xml_lines.append(f"    <loc>{url['loc']}</loc>")
            xml_lines.append(f"    <lastmod>{url['lastmod']}</lastmod>")
            xml_lines.append(f"    <changefreq>{url['changefreq']}</changefreq>")
            xml_lines.append(f"    <priority>{url['priority']}</priority>")
            xml_lines.append("  </url>")
        xml_lines.append("</urlset>")

        output_path = self.output_dir / "sitemap.xml"
        output_path.write_text("\n".join(xml_lines), encoding="utf-8")

    def _generate_rss(self, articles: list):
        """RSSフィード(feed.xml)を生成する"""
        now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0900")

        xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_lines.append('<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">')
        xml_lines.append("  <channel>")
        xml_lines.append(f"    <title>{self._escape_xml(BLOG_NAME)}</title>")
        xml_lines.append(f"    <link>{BLOG_URL}</link>")
        xml_lines.append(
            f"    <description>{self._escape_xml(BLOG_DESCRIPTION)}</description>"
        )
        xml_lines.append(f"    <language>{BLOG_LANGUAGE}</language>")
        xml_lines.append(f"    <lastBuildDate>{now}</lastBuildDate>")
        xml_lines.append(
            f'    <atom:link href="{BLOG_URL}/feed.xml" rel="self" type="application/rss+xml"/>'
        )

        for article in articles[:20]:
            slug = article.get("slug", "untitled")
            title = self._escape_xml(article.get("title", "無題"))
            description = self._escape_xml(
                article.get("description", article.get("title", ""))
            )
            link = f"{BLOG_URL}/articles/{slug}.html"
            date = article.get("date", "")
            category = self._escape_xml(article.get("category", "未分類"))

            xml_lines.append("    <item>")
            xml_lines.append(f"      <title>{title}</title>")
            xml_lines.append(f"      <link>{link}</link>")
            xml_lines.append(f"      <guid>{link}</guid>")
            xml_lines.append(f"      <description>{description}</description>")
            xml_lines.append(f"      <category>{category}</category>")
            if date:
                try:
                    dt = datetime.strptime(date, "%Y-%m-%d")
                    rfc_date = dt.strftime("%a, %d %b %Y 00:00:00 +0900")
                    xml_lines.append(f"      <pubDate>{rfc_date}</pubDate>")
                except ValueError:
                    pass
            xml_lines.append("    </item>")

        xml_lines.append("  </channel>")
        xml_lines.append("</rss>")

        output_path = self.output_dir / "feed.xml"
        output_path.write_text("\n".join(xml_lines), encoding="utf-8")

    # ------------------------------------------------------------------
    # ユーティリティ
    # ------------------------------------------------------------------

    def _group_by_category(self, articles: list) -> dict:
        """記事をカテゴリ別にグループ化する"""
        categories = {}
        for article in articles:
            cat = article.get("category", "未分類")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(article)
        return categories

    @staticmethod
    def _slugify(text: str) -> str:
        """テキストをURL安全なスラッグに変換する（日本語対応）"""
        import re
        import urllib.parse

        slug = re.sub(r"\s+", "-", text.strip())
        return urllib.parse.quote(slug, safe="-_")

    @staticmethod
    def _escape_xml(text: str) -> str:
        """XML特殊文字をエスケープする"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )


# ------------------------------------------------------------------
# 直接実行時
# ------------------------------------------------------------------

if __name__ == "__main__":
    generator = SiteGenerator()
    generator.build_site()
