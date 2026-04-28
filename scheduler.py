"""Quantum Brief - 記事自動生成・投稿スケジューラー

APSchedulerを使って指定時刻に量子コンピューター論文要約記事を自動生成する。
"""
import json
import logging
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from config import SCHEDULE_HOURS, ARTICLES_PER_DAY, TARGET_CATEGORIES, OUTPUT_DIR
from article_generator import ArticleGenerator
from site_generator import SiteGenerator
from seo_optimizer import SEOOptimizer

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# 実行ログ保存ディレクトリ
LOGS_DIR = OUTPUT_DIR / "logs"


class BlogScheduler:
    """量子コンピューター論文要約記事の自動生成スケジューラー"""

    def __init__(self):
        """APScheduler・各モジュールを初期化する"""
        self.scheduler = BlockingScheduler()
        self.article_generator = ArticleGenerator()
        self.site_generator = SiteGenerator()
        self.seo_optimizer = SEOOptimizer()

        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("BlogScheduler を初期化しました")

    def start(self):
        """スケジューラーを開始する"""
        for hour in SCHEDULE_HOURS:
            trigger = CronTrigger(hour=hour, minute=0)
            self.scheduler.add_job(
                self.run_job,
                trigger=trigger,
                id=f"quantum_job_{hour}",
                name=f"量子記事生成ジョブ（{hour}時）",
                misfire_grace_time=3600,
            )
            logger.info(f"ジョブを登録: 毎日 {hour}:00 に記事を生成")

        logger.info(
            f"スケジューラーを開始します（1日{ARTICLES_PER_DAY}記事、"
            f"投稿時刻: {SCHEDULE_HOURS}）"
        )

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("スケジューラーを停止しました")

    def stop(self):
        """スケジューラーを停止する"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("スケジューラーを停止しました")
        else:
            logger.warning("スケジューラーは実行されていません")

    def run_job(self):
        """1回分のジョブを実行する"""
        logger.info("=== ジョブ実行開始 ===")
        start_time = datetime.now()
        result = {
            "timestamp": start_time.isoformat(),
            "status": "started",
            "category": None,
            "keyword": None,
            "article_path": None,
            "seo_score": None,
            "errors": [],
        }

        try:
            # ステップ1: キーワード選定
            logger.info("ステップ1: キーワード選定中...")
            category, keyword = self._select_keyword()
            result["category"] = category
            result["keyword"] = keyword
            logger.info(f"選定結果 - カテゴリ: {category}, キーワード: {keyword}")

            # ステップ2: 記事生成
            logger.info("ステップ2: 記事生成中...")
            article = self.article_generator.generate_article(
                keyword=keyword,
                category=category,
            )
            result["article_path"] = str(article.get("file_path", ""))
            logger.info(f"記事生成完了: {article.get('title', '不明')}")

            # ステップ2.5: アフィリエイトリンク挿入
            logger.info("ステップ2.5: アフィリエイトリンク挿入中...")
            try:
                from affiliate import AffiliateManager
                affiliate_mgr = AffiliateManager()
                article = affiliate_mgr.insert_affiliate_links(article)
                logger.info(f"アフィリエイトリンク: {article.get('affiliate_count', 0)}件挿入")
            except Exception as aff_err:
                logger.warning(f"アフィリエイトリンク挿入をスキップ: {aff_err}")

            # ステップ3: SEOチェック
            logger.info("ステップ3: SEO最適化チェック中...")
            seo_result = self.seo_optimizer.check_seo_score(article)
            result["seo_score"] = seo_result.get("total_score", 0)
            logger.info(f"SEOスコア: {result['seo_score']}")

            if result["seo_score"] < 60:
                logger.warning(
                    f"SEOスコアが低いです（{result['seo_score']}）。"
                    "記事の改善を検討してください。"
                )

            # ステップ4: サイトビルド
            logger.info("ステップ4: サイトビルド中...")
            self.site_generator.build_site()
            logger.info("サイトビルド完了")

            # ステップ5: GitHub Pagesにデプロイ
            logger.info("ステップ5: GitHub Pagesにデプロイ中...")
            try:
                from deployer import GitHubPagesDeployer
                deployer = GitHubPagesDeployer()
                deploy_result = deployer.deploy()
                result["deploy_status"] = deploy_result["status"]
                if "url" in deploy_result:
                    result["deploy_url"] = deploy_result["url"]
                logger.info(f"デプロイ結果: {deploy_result['status']}")
            except Exception as deploy_err:
                logger.warning(f"デプロイをスキップ: {deploy_err}")
                result["deploy_status"] = "skipped"

            result["status"] = "success"
            result["duration_seconds"] = (
                datetime.now() - start_time
            ).total_seconds()
            logger.info(
                f"=== ジョブ完了（{result['duration_seconds']:.1f}秒） ==="
            )

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            result["duration_seconds"] = (
                datetime.now() - start_time
            ).total_seconds()
            logger.error(f"ジョブ実行中にエラー発生: {e}")

        self._log_execution(result)
        return result

    def _select_keyword(self) -> tuple[str, str]:
        """AIを使ってカテゴリとキーワードを選定する

        Returns:
            tuple[str, str]: (カテゴリ名, キーワード)
        """
        from llm import get_llm_client
        from config import GEMINI_API_KEY, GEMINI_MODEL

        client = get_llm_client(__import__('types').SimpleNamespace(GEMINI_API_KEY=GEMINI_API_KEY))

        categories_text = "\n".join(
            f"- {cat}" for cat in TARGET_CATEGORIES
        )

        prompt = (
            "量子コンピューター論文要約ブログ用のキーワードを選定してください。\n\n"
            "以下のカテゴリから1つ選び、そのカテゴリで今注目されている"
            "量子コンピューター関連の研究トピック・キーワードを1つ提案してください。\n\n"
            f"カテゴリ一覧:\n{categories_text}\n\n"
            "忙しいビジネスマンが検索しそうなキーワードを意識してください。\n\n"
            "以下の形式でJSON形式のみで回答してください（説明不要）:\n"
            '{"category": "カテゴリ名", "keyword": "キーワード"}'
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL, contents=prompt
        )

        response_text = response.text.strip()

        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
            response_text = response_text.strip()

        data = json.loads(response_text)
        return data["category"], data["keyword"]

    def _log_execution(self, result: dict):
        """実行ログをJSONファイルに保存する"""
        today = datetime.now().strftime("%Y%m%d")
        log_file = LOGS_DIR / f"{today}.json"

        if log_file.exists():
            with open(log_file, "r", encoding="utf-8") as f:
                logs = json.load(f)
        else:
            logs = []

        logs.append(result)

        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

        logger.info(f"実行ログを保存: {log_file}")


# 直接実行時はスケジューラーを起動
if __name__ == "__main__":
    scheduler = BlogScheduler()
    scheduler.start()
