"""Quantum Brief - 量子コンピューター論文要約ブログ 設定"""
import os
from pathlib import Path

# プロジェクトルート
BASE_DIR = Path(__file__).parent

# Gemini API設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# ブログ設定
BLOG_NAME = "Quantum Brief"
BLOG_DESCRIPTION = "忙しいビジネスマンのための量子コンピューター論文要約ブログ"
BLOG_URL = "/quantum-brief"
BLOG_LANGUAGE = "ja"

# 出力ディレクトリ
OUTPUT_DIR = BASE_DIR / "output"
ARTICLES_DIR = OUTPUT_DIR / "articles"
SITE_DIR = OUTPUT_DIR / "site"

# 記事生成設定
MAX_ARTICLE_LENGTH = 2000  # 3分で読める長さ
ARTICLES_PER_DAY = 3
TARGET_CATEGORIES = [
    "量子コンピューティング基礎",
    "量子アルゴリズム",
    "量子暗号・セキュリティ",
    "量子×ビジネス応用",
    "最新論文レビュー",
]

# SEO設定
MIN_KEYWORD_DENSITY = 1.0  # %
MAX_KEYWORD_DENSITY = 3.0  # %
META_DESCRIPTION_LENGTH = 120  # 文字

# スケジューラー設定
SCHEDULE_HOURS = [8, 12, 18]  # 通勤前・昼休み・退勤時

# ダッシュボード設定
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 8000

# GitHub Pages設定
GITHUB_REPO = os.getenv("GITHUB_REPO", "MuscleLove-777/quantum-brief")
GITHUB_BRANCH = "gh-pages"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Google AdSense設定
ADSENSE_CLIENT_ID = os.getenv("ADSENSE_CLIENT_ID", "")  # 例: "ca-pub-XXXXXXXX"
ADSENSE_ENABLED = bool(ADSENSE_CLIENT_ID)

# アフィリエイト設定
AFFILIATE_LINKS = {
    "量子コンピューティング": [
        {"service": "IBM Quantum", "url": "https://quantum.ibm.com", "description": "IBM量子コンピューティングプラットフォーム"},
        {"service": "Amazon Braket", "url": "https://aws.amazon.com/braket/", "description": "AWS量子コンピューティングサービス"},
    ],
    "オンライン講座": [
        {"service": "Coursera", "url": "https://www.coursera.org", "description": "量子コンピューティング講座"},
        {"service": "edX", "url": "https://www.edx.org", "description": "MITの量子力学コース"},
        {"service": "Udemy", "url": "https://www.udemy.com", "description": "量子プログラミング入門"},
    ],
    "書籍": [
        {"service": "Amazon", "url": "https://www.amazon.co.jp", "description": "量子コンピューター関連書籍"},
        {"service": "楽天ブックス", "url": "https://books.rakuten.co.jp", "description": "量子コンピューター関連書籍"},
    ],
}
AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "")  # 例: "yourtag-22"
