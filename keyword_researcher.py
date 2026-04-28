"""Quantum Brief - 量子コンピューター分野キーワードリサーチモジュール

Gemini APIを使って、量子コンピューター分野のトレンドキーワード提案・
ロングテール分析・競合分析・コンテンツカレンダー生成を行う。
"""
import json
import logging
from datetime import datetime, timedelta

from llm import get_llm_client
from config import GEMINI_API_KEY, GEMINI_MODEL, TARGET_CATEGORIES

logger = logging.getLogger(__name__)


class KeywordResearcher:
    """量子コンピューター分野に特化したキーワードリサーチャー"""

    def __init__(self):
        """Geminiクライアントを初期化する"""
        self.client = get_llm_client(__import__('types').SimpleNamespace(GEMINI_API_KEY=GEMINI_API_KEY))
        self.model_name = GEMINI_MODEL
        logger.info("KeywordResearcher を初期化しました")

    def _call_ai(self, prompt: str, max_tokens: int = 2000) -> str:
        """Gemini APIを呼び出して応答テキストを返す共通メソッド

        Args:
            prompt: ユーザープロンプト
            max_tokens: 最大トークン数

        Returns:
            str: AIの応答テキスト
        """
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        return response.text.strip()

    def _parse_json_response(self, response_text: str) -> any:
        """AIレスポンスからJSONを抽出してパースする

        Args:
            response_text: AIの応答テキスト

        Returns:
            パースされたJSONオブジェクト
        """
        text = response_text.strip()

        # ```json ... ``` ブロックを抽出
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        return json.loads(text)

    def research_trending_keywords(
        self, category: str, count: int = 10
    ) -> list[dict]:
        """量子コンピューター分野のトレンドキーワードをAIで提案する

        Args:
            category: 対象カテゴリ（例: "量子アルゴリズム"）
            count: 提案するキーワード数（デフォルト10）

        Returns:
            list[dict]: 各キーワードの情報を含むリスト
        """
        logger.info(f"トレンドキーワードをリサーチ中: カテゴリ={category}, 件数={count}")

        prompt = (
            f"量子コンピューター分野の「{category}」カテゴリで、"
            f"現在トレンドになっている論文・研究トピック向けの"
            f"ブログ記事キーワードを{count}個提案してください。\n\n"
            "忙しいビジネスマンが検索しそうなキーワードを意識してください。\n\n"
            "各キーワードについて以下の情報を含めてください:\n"
            "- keyword: キーワード\n"
            "- volume: 検索ボリューム予測（「高」「中」「低」のいずれか）\n"
            "- competition: 競合度予測（「高」「中」「低」のいずれか）\n"
            "- article_type: 推奨記事タイプ（例: 論文要約、解説、比較、トレンド分析）\n\n"
            "JSON配列形式のみで回答してください（説明不要）:\n"
            '[{"keyword": "...", "volume": "...", "competition": "...", "article_type": "..."}]'
        )

        response = self._call_ai(prompt)
        keywords = self._parse_json_response(response)

        logger.info(f"{len(keywords)}件のキーワードを取得しました")
        return keywords

    def suggest_long_tail_keywords(self, base_keyword: str) -> list[str]:
        """ベースキーワードからロングテールキーワードを提案する

        Args:
            base_keyword: 元になるキーワード（例: "量子コンピューター"）

        Returns:
            list[str]: ロングテールキーワードのリスト
        """
        logger.info(f"ロングテールキーワードを提案中: {base_keyword}")

        prompt = (
            f"量子コンピューター分野で「{base_keyword}」をベースに、"
            "ビジネスマン向けブログ記事で狙えるロングテールキーワードを10個提案してください。\n\n"
            "検索意図が明確で、3分で読める記事が書きやすいものを優先してください。\n\n"
            "JSON配列形式（文字列の配列）のみで回答してください（説明不要）:\n"
            '["キーワード1", "キーワード2", ...]'
        )

        response = self._call_ai(prompt)
        keywords = self._parse_json_response(response)

        logger.info(f"{len(keywords)}件のロングテールキーワードを取得しました")
        return keywords

    def analyze_competition(self, keyword: str) -> dict:
        """指定キーワードの競合分析をAIで行う

        Args:
            keyword: 分析対象のキーワード

        Returns:
            dict: 競合分析結果
        """
        logger.info(f"競合分析を実行中: {keyword}")

        prompt = (
            f"量子コンピューター分野で「{keyword}」というキーワードでブログ記事を書く場合の"
            "競合分析を行ってください。\n\n"
            "以下の項目を含むJSON形式のみで回答してください（説明不要）:\n"
            "{\n"
            '  "keyword": "対象キーワード",\n'
            '  "difficulty": 難易度（1-10の数値）,\n'
            '  "top_content_types": ["上位表示されやすいコンテンツタイプ"],\n'
            '  "recommended_word_count": 推奨文字数（数値）,\n'
            '  "key_topics": ["記事に含めるべきトピック"],\n'
            '  "differentiation_tips": ["差別化のポイント"]\n'
            "}"
        )

        response = self._call_ai(prompt)
        analysis = self._parse_json_response(response)

        logger.info(f"競合分析完了: 難易度={analysis.get('difficulty', '不明')}")
        return analysis

    def suggest_paper_topics(self, count: int = 5) -> list[dict]:
        """最新の量子コンピューター論文トピックを提案する

        Args:
            count: 提案数

        Returns:
            list[dict]: 論文トピックのリスト
        """
        logger.info(f"論文トピックを提案中: {count}件")

        prompt = (
            f"量子コンピューター分野で最近注目されている研究テーマや論文トピックを"
            f"{count}個提案してください。\n\n"
            "各トピックについて以下の情報を含めてください:\n"
            "- topic: トピック名\n"
            "- description: 概要（50文字以内）\n"
            "- business_relevance: ビジネスとの関連性（50文字以内）\n"
            "- suggested_keyword: ブログ記事のキーワード候補\n"
            "- category: 最適なカテゴリ（以下から選択）\n"
            f"  カテゴリ: {', '.join(TARGET_CATEGORIES)}\n\n"
            "JSON配列形式のみで回答してください（説明不要）:\n"
            '[{"topic": "...", "description": "...", "business_relevance": "...", '
            '"suggested_keyword": "...", "category": "..."}]'
        )

        response = self._call_ai(prompt)
        topics = self._parse_json_response(response)

        logger.info(f"{len(topics)}件の論文トピックを取得しました")
        return topics

    def get_content_calendar(self, days: int = 7) -> list[dict]:
        """指定日数分のコンテンツカレンダーを生成する

        Args:
            days: カレンダーの日数（デフォルト7日）

        Returns:
            list[dict]: 日ごとのコンテンツ計画
        """
        logger.info(f"コンテンツカレンダーを生成中: {days}日分")

        start_date = datetime.now()
        dates = [
            (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(days)
        ]
        dates_text = "\n".join(f"- {d}" for d in dates)

        categories_text = "\n".join(f"- {cat}" for cat in TARGET_CATEGORIES)

        prompt = (
            f"量子コンピューター論文要約ブログのコンテンツカレンダーを"
            "作成してください。\n\n"
            f"日付:\n{dates_text}\n\n"
            f"カテゴリ:\n{categories_text}\n\n"
            "各日付に対して、カテゴリをバランスよく配分し、"
            "最新の量子コンピューター研究トレンドを意識した"
            "キーワードと記事タイプを設定してください。\n\n"
            "忙しいビジネスマンが3分で読める記事を意識してください。\n\n"
            "JSON配列形式のみで回答してください（説明不要）:\n"
            '[{"date": "YYYY-MM-DD", "keyword": "...", '
            '"category": "...", "article_type": "..."}]'
        )

        response = self._call_ai(prompt, max_tokens=3000)
        calendar = self._parse_json_response(response)

        logger.info(f"コンテンツカレンダー生成完了: {len(calendar)}件")
        return calendar


# 直接実行時のテスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    researcher = KeywordResearcher()

    # テスト: トレンドキーワード取得
    print("\n=== トレンドキーワード ===")
    keywords = researcher.research_trending_keywords("量子コンピューティング基礎", count=5)
    for kw in keywords:
        print(f"  {kw['keyword']} (ボリューム: {kw['volume']}, 記事タイプ: {kw['article_type']})")

    # テスト: 論文トピック提案
    print("\n=== 論文トピック提案 ===")
    topics = researcher.suggest_paper_topics(count=3)
    for t in topics:
        print(f"  {t['topic']}: {t['description']}")
