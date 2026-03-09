#!/usr/bin/env python3
"""
対話的要件定義システム
プロジェクト開始前に、ユーザーと対話しながら要件を明確にする
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime

class RequirementsGatherer:
    """要件収集を対話的に行うクラス"""

    def __init__(self):
        self.requirements = {
            "project_info": {},
            "functional_requirements": {},
            "technical_requirements": {},
            "constraints": {},
            "deliverables": {},
            "gathered_at": None
        }

    def gather_game_requirements(self) -> Dict:
        """ゲーム開発用の要件収集"""

        questions = {
            "project_info": [
                {
                    "key": "project_name",
                    "question": "プロジェクト名を教えてください:",
                    "type": "text",
                    "required": True
                },
                {
                    "key": "game_genre",
                    "question": "どのようなジャンルのゲームをお考えですか？\n1. シューティング\n2. パズル\n3. アクション\n4. RPG\n5. シミュレーション\n6. その他",
                    "type": "choice",
                    "options": ["シューティング", "パズル", "アクション", "RPG", "シミュレーション", "その他"],
                    "required": True
                },
                {
                    "key": "target_audience",
                    "question": "対象とするプレイヤー層を教えてください（例: カジュアル、ハードコア、全年齢、大人向け等）:",
                    "type": "text",
                    "required": True
                },
                {
                    "key": "play_time",
                    "question": "想定するプレイ時間は？\n1. 5分以内（カジュアル）\n2. 15-30分（短時間）\n3. 1時間以上（じっくり）",
                    "type": "choice",
                    "options": ["5分以内", "15-30分", "1時間以上"],
                    "required": False
                }
            ],
            "functional_requirements": [
                {
                    "key": "core_mechanics",
                    "question": "ゲームの核となるメカニクスを教えてください（例: 射撃、ジャンプ、パズル解き等）:",
                    "type": "text_list",
                    "required": True
                },
                {
                    "key": "must_have_features",
                    "question": "必須機能を列挙してください（カンマ区切り）:",
                    "type": "text_list",
                    "required": True
                },
                {
                    "key": "nice_to_have_features",
                    "question": "あったら良い機能を列挙してください（カンマ区切り）:",
                    "type": "text_list",
                    "required": False
                },
                {
                    "key": "reference_games",
                    "question": "参考にしたいゲームがあれば教えてください:",
                    "type": "text",
                    "required": False
                }
            ],
            "technical_requirements": [
                {
                    "key": "platform",
                    "question": "対象プラットフォームは？\n1. ブラウザ（Web）\n2. デスクトップ\n3. モバイル\n4. 全プラットフォーム",
                    "type": "choice",
                    "options": ["ブラウザ", "デスクトップ", "モバイル", "全プラットフォーム"],
                    "required": True
                },
                {
                    "key": "tech_stack",
                    "question": "使用したい技術スタックがあれば指定してください（例: Three.js, Phaser, Unity等）:",
                    "type": "text",
                    "required": False,
                    "default": "Three.js"
                },
                {
                    "key": "performance",
                    "question": "パフォーマンス要件は？\n1. 高性能（60FPS必須）\n2. 標準（30FPS以上）\n3. 軽量（低スペックでも動作）",
                    "type": "choice",
                    "options": ["高性能", "標準", "軽量"],
                    "required": False,
                    "default": "標準"
                },
                {
                    "key": "graphics_style",
                    "question": "グラフィックスタイルは？\n1. 3D\n2. 2D\n3. 2.5D（疑似3D）",
                    "type": "choice",
                    "options": ["3D", "2D", "2.5D"],
                    "required": True
                }
            ],
            "constraints": [
                {
                    "key": "timeline",
                    "question": "開発期限はありますか？（例: 2週間、1ヶ月、期限なし）:",
                    "type": "text",
                    "required": False,
                    "default": "期限なし"
                },
                {
                    "key": "budget_constraints",
                    "question": "予算や技術的制約があれば教えてください:",
                    "type": "text",
                    "required": False
                }
            ]
        }

        return questions

    def gather_web_app_requirements(self) -> Dict:
        """Webアプリケーション用の要件収集"""

        questions = {
            "project_info": [
                {
                    "key": "project_name",
                    "question": "プロジェクト名を教えてください:",
                    "type": "text",
                    "required": True
                },
                {
                    "key": "app_type",
                    "question": "どのような種類のWebアプリケーションですか？\n1. SPA（シングルページ）\n2. MPA（マルチページ）\n3. PWA（プログレッシブ）\n4. 静的サイト",
                    "type": "choice",
                    "options": ["SPA", "MPA", "PWA", "静的サイト"],
                    "required": True
                },
                {
                    "key": "target_users",
                    "question": "想定ユーザー数と利用シーンを教えてください:",
                    "type": "text",
                    "required": True
                }
            ],
            "functional_requirements": [
                {
                    "key": "core_features",
                    "question": "コア機能を列挙してください（カンマ区切り）:",
                    "type": "text_list",
                    "required": True
                },
                {
                    "key": "authentication",
                    "question": "認証機能は必要ですか？\n1. 必要（ログイン/ログアウト）\n2. 不要\n3. OAuth連携",
                    "type": "choice",
                    "options": ["必要", "不要", "OAuth連携"],
                    "required": True
                },
                {
                    "key": "database",
                    "question": "データベースは必要ですか？\n1. 必要（リレーショナル）\n2. 必要（NoSQL）\n3. 不要",
                    "type": "choice",
                    "options": ["リレーショナル", "NoSQL", "不要"],
                    "required": True
                }
            ],
            "technical_requirements": [
                {
                    "key": "frontend_framework",
                    "question": "フロントエンドフレームワークの希望は？\n1. React\n2. Vue\n3. Angular\n4. Vanilla JS\n5. その他",
                    "type": "choice",
                    "options": ["React", "Vue", "Angular", "Vanilla JS", "その他"],
                    "required": False,
                    "default": "React"
                },
                {
                    "key": "backend_framework",
                    "question": "バックエンドフレームワークの希望は？\n1. Node.js/Express\n2. Python/Django\n3. Python/FastAPI\n4. 不要（フロントのみ）",
                    "type": "choice",
                    "options": ["Node.js/Express", "Python/Django", "Python/FastAPI", "不要"],
                    "required": False,
                    "default": "Node.js/Express"
                },
                {
                    "key": "responsive",
                    "question": "レスポンシブデザインは必要ですか？",
                    "type": "boolean",
                    "required": True,
                    "default": True
                }
            ],
            "constraints": [
                {
                    "key": "browser_support",
                    "question": "対応ブラウザの要件を教えてください（例: Chrome最新版、IE11対応等）:",
                    "type": "text",
                    "required": False,
                    "default": "モダンブラウザ（Chrome, Firefox, Safari最新版）"
                }
            ]
        }

        return questions

    def generate_requirements_spec(self, answers: Dict) -> str:
        """収集した要件から仕様書を生成"""

        spec = f"""# 要件定義書

## プロジェクト情報
- **プロジェクト名**: {answers.get('project_info', {}).get('project_name', '未定')}
- **作成日**: {datetime.now().strftime('%Y年%m月%d日')}
- **タイプ**: {answers.get('project_info', {}).get('game_genre', answers.get('project_info', {}).get('app_type', '未定'))}

## 機能要件

### 必須機能
"""

        must_haves = answers.get('functional_requirements', {}).get('must_have_features', [])
        if isinstance(must_haves, str):
            must_haves = [f.strip() for f in must_haves.split(',')]

        for feature in must_haves:
            spec += f"- {feature}\n"

        spec += """
### 追加機能（Nice to Have）
"""
        nice_to_haves = answers.get('functional_requirements', {}).get('nice_to_have_features', [])
        if isinstance(nice_to_haves, str):
            nice_to_haves = [f.strip() for f in nice_to_haves.split(',')]

        for feature in nice_to_haves:
            spec += f"- {feature}\n"

        spec += f"""
## 技術要件
- **プラットフォーム**: {answers.get('technical_requirements', {}).get('platform', '未定')}
- **技術スタック**: {answers.get('technical_requirements', {}).get('tech_stack', '未定')}
- **パフォーマンス**: {answers.get('technical_requirements', {}).get('performance', '標準')}

## 制約事項
- **開発期限**: {answers.get('constraints', {}).get('timeline', '期限なし')}
- **その他制約**: {answers.get('constraints', {}).get('budget_constraints', 'なし')}

## 承認
この仕様書に基づいて開発を進めてよろしいですか？
"""

        return spec

    def save_requirements(self, answers: Dict, filepath: str = "requirements.json"):
        """要件をJSONファイルに保存"""

        self.requirements.update(answers)
        self.requirements["gathered_at"] = datetime.now().isoformat()

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.requirements, f, ensure_ascii=False, indent=2)

        return filepath

    def load_requirements(self, filepath: str = "requirements.json") -> Dict:
        """保存された要件を読み込み"""

        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def create_interactive_prompt(self, project_type: str = "game") -> List[Dict]:
        """インタラクティブな質問プロンプトを生成"""

        if project_type == "game":
            questions = self.gather_game_requirements()
        elif project_type == "web_app":
            questions = self.gather_web_app_requirements()
        else:
            raise ValueError(f"Unknown project type: {project_type}")

        prompts = []
        for category, items in questions.items():
            for item in items:
                prompts.append({
                    "category": category,
                    "key": item["key"],
                    "prompt": item["question"],
                    "type": item["type"],
                    "required": item.get("required", False),
                    "default": item.get("default", None),
                    "options": item.get("options", None)
                })

        return prompts