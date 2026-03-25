"""Quantum Brief - SEO最適化モジュール

記事のSEOスコアを分析し、キーワード密度・メタディスクリプション・
見出し構造などの観点から最適化を支援する。
"""

import hashlib
import logging
import re

import config

# ロガー設定
logger = logging.getLogger(__name__)


class SEOOptimizer:
    """記事のSEO最適化を分析・支援するクラス"""

    def __init__(self) -> None:
        """SEOOptimizerを初期化する"""
        self.min_keyword_density = config.MIN_KEYWORD_DENSITY
        self.max_keyword_density = config.MAX_KEYWORD_DENSITY
        self.meta_description_length = config.META_DESCRIPTION_LENGTH
        logger.info("SEOOptimizer を初期化しました")

    def analyze_keyword_density(self, content: str, keyword: str) -> float:
        """本文中のキーワード密度（出現率）を計算する

        Args:
            content: 分析対象の本文テキスト
            keyword: 対象キーワード

        Returns:
            float: キーワード密度（パーセント）
        """
        if not content or not keyword:
            return 0.0

        plain_text = self._strip_markdown(content)

        if len(plain_text) == 0:
            return 0.0

        keyword_lower = keyword.lower()
        text_lower = plain_text.lower()
        count = text_lower.count(keyword_lower)

        density = (count * len(keyword)) / len(plain_text) * 100

        logger.debug(
            "キーワード密度: '%.2f%%（'%s' × %d回 / %d文字）",
            density, keyword, count, len(plain_text),
        )
        return round(density, 2)

    def optimize_meta_description(self, description: str) -> str:
        """メタディスクリプションを最適化する

        Args:
            description: 元のメタディスクリプション

        Returns:
            str: 最適化されたメタディスクリプション
        """
        if not description:
            logger.warning("メタディスクリプションが空です")
            return ""

        optimized = re.sub(r"\s+", " ", description.strip())

        if len(optimized) > self.meta_description_length:
            logger.info(
                "メタディスクリプションを切り詰め: %d文字 → %d文字",
                len(optimized), self.meta_description_length,
            )
            optimized = optimized[: self.meta_description_length - 3] + "..."

        return optimized

    def generate_slug(self, title: str) -> str:
        """記事タイトルからURLスラッグを生成する

        Args:
            title: 記事タイトル

        Returns:
            str: URL用スラッグ
        """
        if not title:
            return "untitled"

        ascii_parts = re.findall(r"[a-zA-Z0-9]+", title)
        title_hash = hashlib.md5(title.encode("utf-8")).hexdigest()[:8]

        if ascii_parts:
            slug_base = "-".join(part.lower() for part in ascii_parts)
            slug = f"{slug_base}-{title_hash}"
        else:
            slug = f"article-{title_hash}"

        max_slug_length = 80
        if len(slug) > max_slug_length:
            slug = slug[:max_slug_length].rstrip("-")

        logger.debug("スラッグ生成: '%s' → '%s'", title, slug)
        return slug

    def check_seo_score(self, article: dict) -> dict:
        """記事のSEOスコアを総合的に算出する

        Args:
            article: 記事データの辞書

        Returns:
            dict: SEO分析結果
        """
        details = {}
        recommendations = []
        keyword = article.get("keyword", "")
        title = article.get("title", "")
        content = article.get("content", "")
        meta_description = article.get("meta_description", "")

        # --- 1. タイトル評価（25点満点） ---
        title_score = 0
        title_length = len(title)

        if 20 <= title_length <= 35:
            title_score += 15
        elif 10 <= title_length <= 45:
            title_score += 10
        elif title_length > 0:
            title_score += 5
            recommendations.append(
                f"タイトルの長さを20〜35文字に調整してください（現在: {title_length}文字）"
            )
        else:
            recommendations.append("タイトルが設定されていません")

        if keyword and keyword.lower() in title.lower():
            title_score += 10
        elif keyword:
            recommendations.append(
                f"タイトルにキーワード「{keyword}」を含めてください"
            )

        details["title"] = {
            "score": title_score,
            "max": 25,
            "length": title_length,
            "has_keyword": keyword.lower() in title.lower() if keyword else False,
        }

        # --- 2. 見出し構造評価（20点満点） ---
        heading_score = 0
        h2_count = len(re.findall(r"^## ", content, re.MULTILINE))
        h3_count = len(re.findall(r"^### ", content, re.MULTILINE))

        if h2_count >= 3:
            heading_score += 10
        elif h2_count >= 1:
            heading_score += 5
            recommendations.append("H2見出しを3つ以上使用することを推奨します")
        else:
            recommendations.append("H2見出しが使用されていません")

        if h3_count >= 2:
            heading_score += 10
        elif h3_count >= 1:
            heading_score += 5
        else:
            recommendations.append("H3見出しを使って内容を細分化することを推奨します")

        details["headings"] = {
            "score": heading_score,
            "max": 20,
            "h2_count": h2_count,
            "h3_count": h3_count,
        }

        # --- 3. キーワード密度評価（20点満点） ---
        kw_score = 0
        if keyword:
            density = self.analyze_keyword_density(content, keyword)

            if self.min_keyword_density <= density <= self.max_keyword_density:
                kw_score = 20
            elif 0.5 <= density <= 4.0:
                kw_score = 12
                if density < self.min_keyword_density:
                    recommendations.append(
                        f"キーワード密度が低いです（{density}%）。"
                        f"{self.min_keyword_density}%以上を目指してください"
                    )
                else:
                    recommendations.append(
                        f"キーワード密度が高すぎます（{density}%）。"
                        f"{self.max_keyword_density}%以下に抑えてください"
                    )
            elif density > 0:
                kw_score = 5
            else:
                recommendations.append(
                    f"キーワード「{keyword}」が本文に含まれていません"
                )

            details["keyword_density"] = {
                "score": kw_score,
                "max": 20,
                "density": density,
                "optimal_range": f"{self.min_keyword_density}%〜{self.max_keyword_density}%",
            }
        else:
            kw_score = 10
            details["keyword_density"] = {
                "score": kw_score,
                "max": 20,
                "note": "キーワード未指定",
            }

        # --- 4. メタディスクリプション評価（20点満点） ---
        meta_score = 0
        meta_length = len(meta_description)

        if 50 <= meta_length <= self.meta_description_length:
            meta_score += 15
        elif 0 < meta_length <= 150:
            meta_score += 8
            recommendations.append(
                f"メタディスクリプションを50〜{self.meta_description_length}文字に"
                f"調整してください（現在: {meta_length}文字）"
            )
        elif meta_length == 0:
            recommendations.append("メタディスクリプションが設定されていません")

        if keyword and keyword.lower() in meta_description.lower():
            meta_score += 5
        elif keyword and meta_description:
            recommendations.append(
                f"メタディスクリプションにキーワード「{keyword}」を含めてください"
            )

        details["meta_description"] = {
            "score": meta_score,
            "max": 20,
            "length": meta_length,
            "has_keyword": (
                keyword.lower() in meta_description.lower()
                if keyword and meta_description
                else False
            ),
        }

        # --- 5. コンテンツ長評価（15点満点） ---
        content_score = 0
        plain_text = self._strip_markdown(content)
        content_length = len(plain_text)

        if content_length >= config.MAX_ARTICLE_LENGTH:
            content_score = 15
        elif content_length >= config.MAX_ARTICLE_LENGTH * 0.7:
            content_score = 10
        elif content_length >= config.MAX_ARTICLE_LENGTH * 0.4:
            content_score = 5
            recommendations.append(
                f"記事の文字数を増やしてください"
                f"（現在: {content_length}文字、目標: {config.MAX_ARTICLE_LENGTH}文字以上）"
            )
        elif content_length > 0:
            content_score = 2
        else:
            recommendations.append("記事の本文が空です")

        details["content_length"] = {
            "score": content_score,
            "max": 15,
            "length": content_length,
            "target": config.MAX_ARTICLE_LENGTH,
        }

        # --- 総合スコア算出 ---
        total_score = (
            title_score + heading_score + kw_score + meta_score + content_score
        )

        result = {
            "total_score": total_score,
            "max_score": 100,
            "grade": self._score_to_grade(total_score),
            "details": details,
            "recommendations": recommendations,
        }

        logger.info(
            "SEOスコア算出: %d/100（%s）- 改善提案%d件",
            total_score, result["grade"], len(recommendations),
        )
        return result

    def suggest_internal_links(
        self, content: str, existing_articles: list
    ) -> list:
        """本文の内容に基づいて内部リンク候補を提案する

        Args:
            content: 現在の記事の本文
            existing_articles: 既存記事データのリスト

        Returns:
            list[dict]: 内部リンク候補のリスト
        """
        if not content or not existing_articles:
            return []

        plain_text = self._strip_markdown(content).lower()
        suggestions = []

        for article in existing_articles:
            relevance = 0.0
            title = article.get("title", "")
            keyword = article.get("keyword", "")
            tags = article.get("tags", [])

            if keyword and keyword.lower() in plain_text:
                relevance += 3.0

            for tag in tags:
                if tag.lower() in plain_text:
                    relevance += 1.0

            title_words = [
                w for w in re.findall(r"[\w]+", title) if len(w) >= 2
            ]
            matched_words = sum(
                1 for w in title_words if w.lower() in plain_text
            )
            if title_words:
                relevance += (matched_words / len(title_words)) * 2.0

            if relevance > 0:
                suggestions.append({
                    "title": title,
                    "slug": article.get("slug", ""),
                    "url": f"{config.BLOG_URL}/articles/{article.get('slug', '')}",
                    "relevance_score": round(relevance, 2),
                })

        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
        top_suggestions = suggestions[:5]

        logger.info(
            "内部リンク候補: %d件中%d件を提案",
            len(suggestions), len(top_suggestions),
        )
        return top_suggestions

    # --- プライベートメソッド ---

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Markdownの装飾記号を除去してプレーンテキストを返す"""
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        text = re.sub(r"`[^`]+`", "", text)
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _score_to_grade(score: int) -> str:
        """数値スコアを評価グレードに変換する"""
        if score >= 90:
            return "S"
        elif score >= 75:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        else:
            return "D"


# --- メインエントリーポイント（テスト・動作確認用） ---

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    optimizer = SEOOptimizer()

    sample_article = {
        "title": "量子超越性とは？Googleの最新成果を3分で解説",
        "keyword": "量子超越性",
        "content": """# 量子超越性とは？Googleの最新成果を3分で解説

## 3行でわかるポイント
- 量子超越性（量子コンピューターが従来のコンピューターを超える性能を示すこと）が実証された
- Googleの量子プロセッサが従来のスパコンでは1万年かかる計算を200秒で完了
- 量子超越性の実現は暗号技術や創薬分野に大きな影響を与える

## わかりやすく解説
量子超越性とは、量子コンピューターが従来のスーパーコンピューターでは
実質的に解けない問題を解ける能力のことです。

### なぜすごいのか
従来のコンピューターは0と1の2つの状態しか扱えませんが、
量子コンピューターは「量子ビット（キュービット）」という特殊な仕組みで
0と1を同時に扱えます。

## ビジネスへの影響
量子超越性が実用化されれば、創薬、金融、物流など幅広い分野で革新が起きます。

## 編集部の一言
量子超越性はまだ研究段階ですが、ビジネスマンとして動向を把握しておく価値は大きいです。
""",
        "meta_description": "量子超越性とは何か？Googleの最新成果をビジネスマン向けに3分で解説。量子コンピューターが従来型を超える理由とビジネスへの影響を紹介。",
        "tags": ["量子超越性", "量子コンピューター", "Google", "量子ビット", "量子技術"],
    }

    print("=== SEOスコア分析 ===")
    result = optimizer.check_seo_score(sample_article)
    print(f"総合スコア: {result['total_score']}/100（グレード: {result['grade']}）")
