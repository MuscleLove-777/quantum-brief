"""Quantum Brief - アフィリエイトリンク自動挿入モジュール

量子コンピューター関連の書籍・講座へのリンクを自動挿入する。
"""
import logging
from config import AFFILIATE_LINKS, AFFILIATE_TAG, ADSENSE_CLIENT_ID, ADSENSE_ENABLED

logger = logging.getLogger(__name__)


class AffiliateManager:
    """アフィリエイトリンクの管理と自動挿入を行うクラス"""

    def __init__(self):
        """アフィリエイト設定を読み込む"""
        self.links = AFFILIATE_LINKS
        self.amazon_tag = AFFILIATE_TAG
        self.adsense_id = ADSENSE_CLIENT_ID
        self.adsense_enabled = ADSENSE_ENABLED

    def insert_affiliate_links(self, article: dict) -> dict:
        """記事にアフィリエイトリンクを自動挿入する

        Args:
            article: 記事データ辞書

        Returns:
            dict: アフィリエイトリンクが追加された記事データ
        """
        content = article.get("content", "")
        category = article.get("category", "")
        keyword = article.get("keyword", "")

        relevant_links = self._find_relevant_links(category, keyword)

        if relevant_links:
            affiliate_section = self._build_affiliate_section(relevant_links)

            # 編集部の一言セクションの前に挿入（なければ末尾）
            if "## 編集部の一言" in content:
                content = content.replace(
                    "## 編集部の一言",
                    f"{affiliate_section}\n\n## 編集部の一言"
                )
            elif "## まとめ" in content:
                content = content.replace(
                    "## まとめ",
                    f"{affiliate_section}\n\n## まとめ"
                )
            else:
                content += f"\n\n{affiliate_section}"

            article["content"] = content
            article["has_affiliate"] = True
            article["affiliate_count"] = len(relevant_links)
            logger.info(f"{len(relevant_links)}件のアフィリエイトリンクを挿入しました")
        else:
            article["has_affiliate"] = False
            article["affiliate_count"] = 0

        return article

    def _find_relevant_links(self, category: str, keyword: str) -> list:
        """カテゴリとキーワードに関連するアフィリエイトリンクを取得する

        Args:
            category: 記事のカテゴリ
            keyword: 記事のキーワード

        Returns:
            list: 関連するアフィリエイトリンクのリスト
        """
        relevant = []

        for link_category, links in self.links.items():
            if (link_category in category or
                link_category in keyword or
                category in link_category or
                "量子" in link_category):
                relevant.extend(links)

        # 書籍は常に追加
        if "書籍" in self.links and not any(l.get("service") == "Amazon" for l in relevant):
            relevant.extend(self.links["書籍"])

        # オンライン講座も追加
        if "オンライン講座" in self.links and not any(l.get("service") == "Coursera" for l in relevant):
            relevant.extend(self.links["オンライン講座"])

        # 重複除去
        seen = set()
        unique = []
        for link in relevant:
            if link["service"] not in seen:
                seen.add(link["service"])
                unique.append(link)

        return unique[:5]

    def _build_affiliate_section(self, links: list) -> str:
        """アフィリエイトリンクセクションのMarkdownを生成する

        Args:
            links: アフィリエイトリンクのリスト

        Returns:
            str: Markdown形式のおすすめセクション
        """
        section = "## もっと学びたい方へ\n\n"
        section += "量子コンピューターについてさらに深く学びたい方には、以下のリソースがおすすめです。\n\n"

        for link in links:
            url = link["url"]
            if "amazon" in url.lower() and self.amazon_tag:
                separator = "&" if "?" in url else "?"
                url = f"{url}{separator}tag={self.amazon_tag}"

            section += f"- **[{link['service']}]({url})** - {link['description']}\n"

        section += "\n*※ 上記リンクからご利用いただくと、サイト運営の支援になります。*\n"
        return section

    def get_adsense_head_tag(self) -> str:
        """AdSenseの<head>タグ用スクリプトを返す"""
        if not self.adsense_enabled:
            return ""

        return f"""<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={self.adsense_id}" crossorigin="anonymous"></script>"""

    def get_adsense_article_ad(self) -> str:
        """記事内広告用のAdSenseコードを返す"""
        if not self.adsense_enabled:
            return ""

        return f"""
<div style="text-align:center;margin:24px 0;">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="{self.adsense_id}"
       data-ad-slot="auto"
       data-ad-format="auto"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>"""

    def get_adsense_sidebar_ad(self) -> str:
        """サイドバー広告用のAdSenseコードを返す"""
        if not self.adsense_enabled:
            return ""

        return f"""
<div style="margin:20px 0;">
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client="{self.adsense_id}"
       data-ad-slot="auto"
       data-ad-format="rectangle"
       data-full-width-responsive="true"></ins>
  <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>"""


# 直接実行時のテスト
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    manager = AffiliateManager()

    test_article = {
        "title": "量子超越性とは？3分でわかる解説",
        "content": "# 量子超越性とは？\n\n本記事では量子超越性について解説します。\n\n## わかりやすく解説\n\n量子コンピューターの基礎です。\n\n## 編集部の一言\n\n量子の世界は奥が深いですね。",
        "category": "量子コンピューティング基礎",
        "keyword": "量子超越性",
    }

    result = manager.insert_affiliate_links(test_article)
    print("=== アフィリエイト挿入テスト ===")
    print(f"リンク数: {result['affiliate_count']}")
    print(f"\n--- 記事内容（末尾部分） ---")
    print(result["content"][-500:])
