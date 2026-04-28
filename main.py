"""Quantum Brief - メインエントリーポイント

argparseを使ったCLIインターフェース。

使い方:
    python main.py generate --keyword "量子超越性" --category "量子コンピューティング基礎"
    python main.py schedule
    python main.py build
    python main.py keywords --category "量子アルゴリズム"
    python main.py calendar --days 7
    python main.py dashboard
"""
import argparse
import json
import logging
import sys
from llm import get_llm_client

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_generate(args):
    """単発で量子コンピューター論文要約記事を生成する"""
    from article_generator import ArticleGenerator
    from seo_optimizer import SEOOptimizer

    print(f"\n量子コンピューター論文要約記事を生成します...")
    print(f"  キーワード: {args.keyword}")
    print(f"  カテゴリ: {args.category}")
    print()

    generator = ArticleGenerator()
    article = generator.generate_article(keyword=args.keyword, category=args.category)

    print(f"記事生成完了!")
    print(f"  タイトル: {article.get('title', '不明')}")
    print(f"  保存先: {article.get('file_path', '不明')}")

    optimizer = SEOOptimizer()
    seo_result = optimizer.check_seo_score(article)
    print(f"  SEOスコア: {seo_result.get('total_score', '不明')}")
    print()


def cmd_schedule(args):
    """スケジューラーを起動する"""
    from scheduler import BlogScheduler
    from config import SCHEDULE_HOURS, ARTICLES_PER_DAY

    print("\nスケジューラーを起動します")
    print(f"  投稿時刻: {SCHEDULE_HOURS}")
    print(f"  1日の記事数: {ARTICLES_PER_DAY}")
    print("  停止するには Ctrl+C を押してください")
    print()

    scheduler = BlogScheduler()
    scheduler.start()


def cmd_build(args):
    """サイトをビルドする"""
    from site_generator import SiteGenerator

    print("\nサイトをビルドします...")

    generator = SiteGenerator()
    generator.build_site()

    print("サイトビルド完了!")
    print()


def cmd_keywords(args):
    """キーワードリサーチを実行する"""
    from keyword_researcher import KeywordResearcher

    category = args.category
    count = args.count

    print(f"\n量子コンピューター分野のキーワードリサーチを実行します...")
    print(f"  カテゴリ: {category}")
    print(f"  取得件数: {count}")
    print()

    researcher = KeywordResearcher()

    print("--- トレンドキーワード ---")
    keywords = researcher.research_trending_keywords(category, count=count)
    for i, kw in enumerate(keywords, 1):
        print(
            f"  {i:2d}. {kw['keyword']}"
            f"  [ボリューム: {kw.get('volume', '-')}"
            f" | 競合: {kw.get('competition', '-')}"
            f" | タイプ: {kw.get('article_type', '-')}]"
        )
    print()

    if keywords:
        base = keywords[0]["keyword"]
        print(f"--- ロングテールキーワード（ベース: {base}） ---")
        long_tail = researcher.suggest_long_tail_keywords(base)
        for i, lt in enumerate(long_tail, 1):
            print(f"  {i:2d}. {lt}")
        print()

    if keywords:
        base = keywords[0]["keyword"]
        print(f"--- 競合分析（{base}） ---")
        analysis = researcher.analyze_competition(base)
        print(f"  難易度: {analysis.get('difficulty', '-')}/10")
        print(f"  推奨文字数: {analysis.get('recommended_word_count', '-')}文字")
        topics = analysis.get("key_topics", [])
        if topics:
            print(f"  含めるべきトピック:")
            for t in topics:
                print(f"    - {t}")
        tips = analysis.get("differentiation_tips", [])
        if tips:
            print(f"  差別化のポイント:")
            for t in tips:
                print(f"    - {t}")
        print()


def cmd_calendar(args):
    """コンテンツカレンダーを生成する"""
    from keyword_researcher import KeywordResearcher

    days = args.days

    print(f"\nコンテンツカレンダーを生成します（{days}日分）...")
    print()

    researcher = KeywordResearcher()
    calendar = researcher.get_content_calendar(days=days)

    print("--- コンテンツカレンダー ---")
    print(f"{'日付':<14} {'カテゴリ':<20} {'キーワード':<30} {'記事タイプ'}")
    print("-" * 80)
    for entry in calendar:
        print(
            f"{entry.get('date', '-'):<14} "
            f"{entry.get('category', '-'):<20} "
            f"{entry.get('keyword', '-'):<30} "
            f"{entry.get('article_type', '-')}"
        )
    print()

    if args.output:
        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(calendar, f, ensure_ascii=False, indent=2)
        print(f"カレンダーを保存しました: {output_path}")
        print()


def cmd_deploy(args):
    """GitHub Pagesにデプロイする"""
    from deployer import GitHubPagesDeployer

    print("\nGitHub Pagesにデプロイします...")
    deployer = GitHubPagesDeployer()

    status = deployer.check_status()
    print(f"  リポジトリ: {status['repo']}")
    print(f"  ブランチ: {status['branch']}")
    print(f"  公開URL: {status['url']}")
    print()

    result = deployer.deploy()
    print(f"  結果: {result['status']}")
    print(f"  メッセージ: {result['message']}")
    if "url" in result:
        print(f"  URL: {result['url']}")
    print()


def cmd_dashboard(args):
    """ダッシュボードを起動する"""
    from config import DASHBOARD_HOST, DASHBOARD_PORT

    print(f"\nダッシュボードを起動します...")
    print(f"  URL: http://{DASHBOARD_HOST}:{DASHBOARD_PORT}")
    print("  停止するには Ctrl+C を押してください")
    print()

    import uvicorn
    from dashboard import app
    uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT)


def main():
    """CLIのメインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Quantum Brief - 量子コンピューター論文要約ブログ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "使用例:\n"
            '  python main.py generate --keyword "量子超越性" --category "量子コンピューティング基礎"\n'
            "  python main.py schedule\n"
            "  python main.py build\n"
            '  python main.py keywords --category "量子アルゴリズム"\n'
            "  python main.py calendar --days 7\n"
            "  python main.py dashboard"
        ),
    )
    subparsers = parser.add_subparsers(
        dest="command",
        help="実行するコマンド",
    )

    # generate コマンド
    parser_gen = subparsers.add_parser("generate", help="単発で記事を生成する")
    parser_gen.add_argument("--keyword", required=True, help="記事のターゲットキーワード")
    parser_gen.add_argument("--category", required=True, help="記事のカテゴリ")
    parser_gen.set_defaults(func=cmd_generate)

    # schedule コマンド
    parser_sched = subparsers.add_parser("schedule", help="記事自動生成スケジューラーを起動する")
    parser_sched.set_defaults(func=cmd_schedule)

    # build コマンド
    parser_build = subparsers.add_parser("build", help="サイトをビルドする")
    parser_build.set_defaults(func=cmd_build)

    # keywords コマンド
    parser_kw = subparsers.add_parser("keywords", help="キーワードリサーチを実行する")
    parser_kw.add_argument("--category", required=True, help="リサーチ対象のカテゴリ")
    parser_kw.add_argument("--count", type=int, default=10, help="取得するキーワード数（デフォルト: 10）")
    parser_kw.set_defaults(func=cmd_keywords)

    # calendar コマンド
    parser_cal = subparsers.add_parser("calendar", help="コンテンツカレンダーを生成する")
    parser_cal.add_argument("--days", type=int, default=7, help="カレンダーの日数（デフォルト: 7）")
    parser_cal.add_argument("--output", help="カレンダーをJSONファイルに保存するパス（省略可）")
    parser_cal.set_defaults(func=cmd_calendar)

    # deploy コマンド
    parser_deploy = subparsers.add_parser("deploy", help="GitHub Pagesにデプロイする")
    parser_deploy.set_defaults(func=cmd_deploy)

    # dashboard コマンド
    parser_dash = subparsers.add_parser("dashboard", help="ダッシュボードを起動する")
    parser_dash.set_defaults(func=cmd_dashboard)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
