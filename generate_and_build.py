"""Quantum Brief - GitHub Actions用スクリプト

キーワード選定 → 記事生成 → サイトビルドを一括で実行する。
GitHub Actionsのワークフローから呼び出される。
"""
import json
import logging
import sys
import time
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """メイン処理: キーワード選定 → 記事生成 → サイトビルド"""
    logger.info("=== Quantum Brief 自動生成開始 ===")
    start_time = datetime.now()

    # ステップ1: キーワード選定
    logger.info("ステップ1: キーワード選定")
    try:
        from llm import get_llm_client
        from config import GEMINI_API_KEY, GEMINI_MODEL, TARGET_CATEGORIES

        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY が設定されていません")
            sys.exit(1)

        client = genai.Client(api_key=GEMINI_API_KEY)

        categories_text = "\n".join(f"- {cat}" for cat in TARGET_CATEGORIES)
        prompt = (
            "量子コンピューター論文要約ブログ用のキーワードを選定してください。\n\n"
            "以下のカテゴリから1つ選び、そのカテゴリで今注目されている"
            "量子コンピューター関連の研究トピック・キーワードを1つ提案してください。\n\n"
            f"カテゴリ一覧:\n{categories_text}\n\n"
            "忙しいビジネスマンが検索しそうなキーワードを意識してください。\n\n"
            "以下の形式でJSON形式のみで回答してください（説明不要）:\n"
            '{"category": "カテゴリ名", "keyword": "キーワード"}'
        )

        max_retries = 5
        response = None
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL, contents=prompt
                )
                break
            except Exception as api_err:
                err_str = str(api_err)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    wait_time = 60 * (attempt + 1)  # 60s, 120s, 180s, ...
                    logger.warning(
                        "レート制限エラー（試行 %d/%d）。%d秒後にリトライします...",
                        attempt + 1, max_retries, wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    raise
        if response is None:
            raise RuntimeError("レート制限エラーが続き、最大リトライ回数に達しました")
        response_text = response.text.strip()

        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        data = json.loads(response_text)
        category = data["category"]
        keyword = data["keyword"]
        logger.info(f"選定結果 - カテゴリ: {category}, キーワード: {keyword}")

    except Exception as e:
        logger.error(f"キーワード選定に失敗: {e}")
        sys.exit(1)

    # ステップ2: 記事生成
    logger.info("ステップ2: 記事生成")
    try:
        from article_generator import ArticleGenerator
        from seo_optimizer import SEOOptimizer

        generator = ArticleGenerator()
        article = generator.generate_article(keyword=keyword, category=category)
        logger.info(f"記事生成完了: {article.get('title', '不明')}")

        # SEOスコアチェック
        optimizer = SEOOptimizer()
        seo_result = optimizer.check_seo_score(article)
        logger.info(f"SEOスコア: {seo_result.get('total_score', 0)}/100")

    except Exception as e:
        logger.error(f"記事生成に失敗: {e}")
        sys.exit(1)

    # ステップ2.5: アフィリエイトリンク挿入
    logger.info("ステップ2.5: アフィリエイトリンク挿入")
    try:
        from affiliate import AffiliateManager
        affiliate_mgr = AffiliateManager()
        article = affiliate_mgr.insert_affiliate_links(article)
        logger.info(f"アフィリエイトリンク: {article.get('affiliate_count', 0)}件挿入")
    except Exception as aff_err:
        logger.warning(f"アフィリエイトリンク挿入をスキップ: {aff_err}")

    # ステップ3: サイトビルド
    logger.info("ステップ3: サイトビルド")
    try:
        from site_generator import SiteGenerator
        site_gen = SiteGenerator()
        site_gen.build_site()
        logger.info("サイトビルド完了")
    except Exception as e:
        logger.error(f"サイトビルドに失敗: {e}")
        sys.exit(1)

    # 完了
    duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"=== 自動生成完了（{duration:.1f}秒） ===")
    logger.info(f"  カテゴリ: {category}")
    logger.info(f"  キーワード: {keyword}")
    logger.info(f"  タイトル: {article.get('title', '不明')}")
    logger.info(f"  SEOスコア: {seo_result.get('total_score', 0)}/100")


if __name__ == "__main__":
    main()
