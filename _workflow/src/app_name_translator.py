#!/usr/bin/env python3
"""
🌐 アプリ名翻訳ツール
日本語のアプリ名を英語のslug形式に変換します。

使用方法:
    python3 app_name_translator.py "タスク管理アプリ"
    → task-manager

    python3 app_name_translator.py "シューティングゲーム"
    → shooting-game

Claude API を使用して自然な英語名に変換します。
"""

import os
import sys
import re
import json
from pathlib import Path

def load_api_key() -> str:
    """ANTHROPIC_API_KEY を取得（複数ソースから探索）"""

    # 1. 環境変数
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        return api_key

    # 2. グローバル設定ファイル（~/.config/ai-agents/profiles/default.env）
    global_env = Path.home() / ".config" / "ai-agents" / "profiles" / "default.env"
    if global_env.exists():
        try:
            with open(global_env, 'r') as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        return line.split('=', 1)[1].strip().strip('"').strip("'")
        except:
            pass

    # 3. ローカル .env ファイル
    local_env = Path('.env')
    if local_env.exists():
        try:
            with open(local_env, 'r') as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        return line.split('=', 1)[1].strip().strip('"').strip("'")
        except:
            pass

    # 4. ホームディレクトリの .env
    home_env = Path.home() / '.env'
    if home_env.exists():
        try:
            with open(home_env, 'r') as f:
                for line in f:
                    if line.startswith('ANTHROPIC_API_KEY='):
                        return line.split('=', 1)[1].strip().strip('"').strip("'")
        except:
            pass

    return None


def is_japanese(text: str) -> bool:
    """テキストに日本語が含まれているかチェック"""
    # ひらがな、カタカナ、漢字のUnicode範囲
    japanese_pattern = re.compile(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]')
    return bool(japanese_pattern.search(text))


def translate_with_claude(japanese_name: str, api_key: str) -> dict:
    """Claude API を使って日本語を英語のアプリ名に変換"""
    import urllib.request
    import urllib.error

    prompt = f"""以下の日本語のアプリ/ゲーム名を、英語のslug形式（ハイフン区切り、小文字）に変換してください。

日本語名: {japanese_name}

要件:
1. 意味を保持した自然な英語に翻訳
2. slug形式（小文字、ハイフン区切り、英数字のみ）
3. 簡潔で分かりやすい名前（2-4語程度）
4. 一般的なアプリ/ゲーム名として自然

出力形式（JSON）:
{{
  "english_name": "Task Manager",
  "slug": "task-manager",
  "alternatives": ["todo-app", "task-tracker"]
}}

JSONのみを出力してください。説明は不要です。"""

    request_body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 256,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(request_body).encode('utf-8'),
            headers=headers,
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result['content'][0]['text']

            # JSONを抽出（コードブロックがある場合に対応）
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            return json.loads(content.strip())

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        raise Exception(f"API Error ({e.code}): {error_body}")
    except json.JSONDecodeError as e:
        raise Exception(f"JSON Parse Error: {content}")


def simple_transliterate(japanese_name: str) -> str:
    """簡易的なローマ字変換（API使用不可時のフォールバック）"""
    # 一般的なアプリ名のマッピング（日本語→英語+マーカー）
    # マーカー(--)を使って単語境界を示す
    common_mappings = {
        # 基本
        'タスク': 'task',
        '管理': 'manager',
        'アプリ': 'app',
        'ゲーム': 'game',
        'ツール': 'tool',
        'システム': 'system',
        'サービス': 'service',

        # 乗り物・レース
        '車': 'car',
        'カー': 'car',
        '自動車': 'car',
        'レース': 'race',
        '競争': 'race',
        '競走': 'race',
        'レーシング': 'racing',
        'ドライブ': 'drive',
        'ドライビング': 'driving',
        '運転': 'driving',
        'バイク': 'bike',
        'オートバイ': 'motorcycle',
        '自転車': 'bicycle',
        '電車': 'train',
        '飛行機': 'airplane',
        'ヘリコプター': 'helicopter',
        '船': 'ship',
        'ボート': 'boat',
        'ロケット': 'rocket',

        # ゲームジャンル
        'シューティング': 'shooting',
        'パズル': 'puzzle',
        'クイズ': 'quiz',
        'RPG': 'rpg',
        'アクション': 'action',
        'アドベンチャー': 'adventure',
        'ストラテジー': 'strategy',
        '戦略': 'strategy',
        'シミュレーション': 'simulation',
        'スポーツ': 'sports',
        'カード': 'card',
        'ボード': 'board',
        'パーティー': 'party',
        'マルチプレイヤー': 'multiplayer',
        'オンライン': 'online',
        'オフライン': 'offline',
        'ミニ': 'mini',
        'アーケード': 'arcade',
        'レトロ': 'retro',
        'ピクセル': 'pixel',
        'ドット': 'pixel',
        'クリッカー': 'clicker',
        'アイドル': 'idle',
        '放置': 'idle',
        'マージ': 'merge',
        '合体': 'merge',
        'マッチ': 'match',
        'ブロック': 'block',
        'テトリス': 'tetris',
        'ソリティア': 'solitaire',
        '麻雀': 'mahjong',
        '将棋': 'shogi',
        '囲碁': 'go',
        'チェス': 'chess',
        'オセロ': 'othello',
        'ホラー': 'horror',
        '恐怖': 'horror',
        'ミステリー': 'mystery',
        '謎': 'mystery',
        'サバイバル': 'survival',
        '生存': 'survival',
        'ディフェンス': 'defense',
        '防衛': 'defense',
        'タワー': 'tower',
        'ランナー': 'runner',
        'ジャンプ': 'jump',
        'フライト': 'flight',
        '飛行': 'flight',
        'ダイビング': 'diving',

        # 宇宙・SF
        '宇宙': 'space',
        'スペース': 'space',
        '侵略者': 'invaders',
        'インベーダー': 'invaders',
        'エイリアン': 'alien',
        '宇宙人': 'alien',
        'ロボット': 'robot',
        'メカ': 'mecha',
        '未来': 'future',
        'サイバー': 'cyber',

        # 動物・自然
        '動物': 'animal',
        'アニマル': 'animal',
        '犬': 'dog',
        '猫': 'cat',
        '鳥': 'bird',
        '魚': 'fish',
        'ドラゴン': 'dragon',
        '竜': 'dragon',
        'モンスター': 'monster',
        '怪獣': 'monster',
        '恐竜': 'dinosaur',
        '森': 'forest',
        '海': 'ocean',
        '山': 'mountain',
        '川': 'river',
        '空': 'sky',
        '島': 'island',
        '世界': 'world',
        '王国': 'kingdom',
        '城': 'castle',
        'ダンジョン': 'dungeon',
        '迷宮': 'maze',

        # 戦闘・アクション
        '戦い': 'battle',
        'バトル': 'battle',
        '戦争': 'war',
        'ウォー': 'war',
        '戦士': 'warrior',
        'ウォリアー': 'warrior',
        '勇者': 'hero',
        'ヒーロー': 'hero',
        '冒険': 'adventure',
        '冒険者': 'adventurer',
        '剣': 'sword',
        '魔法': 'magic',
        'マジック': 'magic',
        '忍者': 'ninja',
        '侍': 'samurai',
        '騎士': 'knight',
        '海賊': 'pirate',

        # 日常アプリ
        'チャット': 'chat',
        'メモ': 'memo',
        'ノート': 'note',
        '計算': 'calc',
        '電卓': 'calculator',
        'カレンダー': 'calendar',
        '天気': 'weather',
        '音楽': 'music',
        '写真': 'photo',
        '動画': 'video',
        'ニュース': 'news',
        'ショッピング': 'shopping',
        '買い物': 'shopping',
        'レシピ': 'recipe',
        '料理': 'cooking',
        '健康': 'health',
        '運動': 'fitness',
        '睡眠': 'sleep',
        '日記': 'diary',
        '家計簿': 'budget',
        'TODO': 'todo',
        'やること': 'todo',
        'リスト': 'list',
        'トラッカー': 'tracker',
        '追跡': 'tracker',
        'ボット': 'bot',
        'AI': 'ai',
        'ポートフォリオ': 'portfolio',
        'ブログ': 'blog',
        'SNS': 'social',
        '翻訳': 'translator',
        '辞書': 'dictionary',
        '学習': 'learning',
        '勉強': 'study',
        '英語': 'english',
        '数学': 'math',
        'プログラミング': 'coding',
        'コード': 'code',
        'エディタ': 'editor',
        'ビューア': 'viewer',
        'プレイヤー': 'player',
        'ブラウザ': 'browser',
        'ランチャー': 'launcher',
        'ウィジェット': 'widget',
        'ダッシュボード': 'dashboard',
        'モニター': 'monitor',
        'アナライザー': 'analyzer',
        '分析': 'analytics',
        'レポート': 'report',
        'チャート': 'chart',
        'グラフ': 'graph',
        'マップ': 'map',
        '地図': 'map',
        'ナビ': 'navi',
        '検索': 'search',
        'ファインダー': 'finder',
        'スキャナー': 'scanner',
        'コンバーター': 'converter',
        '変換': 'converter',
        'ジェネレーター': 'generator',
        '生成': 'generator',
        'シミュレーター': 'simulator',
        'エミュレーター': 'emulator',
        'テスター': 'tester',
        'デバッガー': 'debugger',
        'ロガー': 'logger',
        'バックアップ': 'backup',
        'シンク': 'sync',
        '同期': 'sync',
        'クラウド': 'cloud',
        'ストレージ': 'storage',
        'ファイル': 'file',
        'フォルダ': 'folder',
        'ドキュメント': 'docs',
        'スプレッドシート': 'spreadsheet',
        'プレゼン': 'slides',
        'スライド': 'slides',
        'ホワイトボード': 'whiteboard',
        'ノートブック': 'notebook',
        'ジャーナル': 'journal',
        'タイマー': 'timer',
        'ストップウォッチ': 'stopwatch',
        'アラーム': 'alarm',
        'リマインダー': 'reminder',
        'スケジューラー': 'scheduler',
        'プランナー': 'planner',
        'オーガナイザー': 'organizer',
        'ポモドーロ': 'pomodoro',
        'フォーカス': 'focus',
        '集中': 'focus',
    }

    result = japanese_name

    # 長いキーワードから順にマッチさせるためソート
    sorted_mappings = sorted(common_mappings.items(), key=lambda x: len(x[0]), reverse=True)

    # 各日本語キーワードを英語に置換（境界マーカー付き）
    for jp, en in sorted_mappings:
        # 大文字小文字を無視してマッチ
        pattern = re.compile(re.escape(jp), re.IGNORECASE)
        result = pattern.sub(f'-{en}-', result)

    # 残った日本語文字を削除
    result = re.sub(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', '', result)

    # 小文字化
    result = result.lower()

    # slug形式に正規化（連続ハイフンを1つに、先頭末尾のハイフンを削除）
    result = re.sub(r'[^a-z0-9]+', '-', result)
    result = re.sub(r'-+', '-', result)
    result = result.strip('-')

    return result if result else 'my-app'


def main():
    if len(sys.argv) < 2:
        print("使用方法: python3 app_name_translator.py <アプリ名>", file=sys.stderr)
        sys.exit(1)

    input_name = ' '.join(sys.argv[1:])

    # 日本語チェック
    if not is_japanese(input_name):
        # 既に英語の場合はslug変換のみ
        slug = input_name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')
        print(json.dumps({
            "original": input_name,
            "english_name": input_name,
            "slug": slug,
            "is_translated": False
        }))
        sys.exit(0)

    # API キーを取得
    api_key = load_api_key()

    if api_key:
        try:
            result = translate_with_claude(input_name, api_key)
            result["original"] = input_name
            result["is_translated"] = True
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(0)
        except Exception as e:
            print(f"API Error: {e}", file=sys.stderr)
            # フォールバックへ

    # フォールバック: 簡易変換
    slug = simple_transliterate(input_name)
    print(json.dumps({
        "original": input_name,
        "english_name": slug.replace('-', ' ').title(),
        "slug": slug,
        "is_translated": True,
        "fallback": True
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
