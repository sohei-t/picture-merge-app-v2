#!/usr/bin/env python3
"""
ビジュアルドキュメント生成システム
プロジェクトの成果物を視覚的に見やすいHTMLと解説台本として生成
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import base64

class DocumentationGenerator:
    """ドキュメント生成クラス"""

    def __init__(self, project_name: str = "Project"):
        self.project_name = project_name
        self.sections = []
        self.narration_script = []

    def generate_visual_html(self,
                           project_data: Dict,
                           screenshots: List[str] = None,
                           include_narration: bool = True) -> str:
        """視覚的に見やすいHTMLドキュメントを生成"""

        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.project_name} - プロジェクト解説</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Helvetica Neue', Arial, 'Hiragino Sans', 'Meiryo', sans-serif;
            line-height: 1.8;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .hero {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            padding: 60px;
            text-align: center;
            color: white;
            position: relative;
        }}

        .hero h1 {{
            font-size: 3.5em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
            animation: fadeInUp 1s ease;
        }}

        .hero p {{
            font-size: 1.4em;
            opacity: 0.95;
            animation: fadeInUp 1s ease 0.2s;
            animation-fill-mode: both;
        }}

        .section {{
            padding: 60px;
            border-bottom: 1px solid #e0e0e0;
            animation: fadeIn 0.8s ease;
        }}

        .section:last-child {{
            border-bottom: none;
        }}

        .section h2 {{
            font-size: 2.5em;
            color: #667eea;
            margin-bottom: 30px;
            position: relative;
            padding-left: 20px;
        }}

        .section h2:before {{
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 5px;
            height: 40px;
            background: linear-gradient(to bottom, #667eea, #764ba2);
            border-radius: 3px;
        }}

        .feature-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }}

        .feature-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}

        .feature-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
        }}

        .feature-card h3 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}

        .feature-card .icon {{
            font-size: 2.5em;
            margin-bottom: 20px;
        }}

        .tech-stack {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 30px;
        }}

        .tech-badge {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
            transition: transform 0.3s ease;
        }}

        .tech-badge:hover {{
            transform: scale(1.05);
        }}

        .screenshot-gallery {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }}

        .screenshot {{
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s ease;
            cursor: pointer;
        }}

        .screenshot:hover {{
            transform: scale(1.05);
        }}

        .screenshot img {{
            width: 100%;
            height: auto;
            display: block;
        }}

        .timeline {{
            position: relative;
            padding: 40px 0;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            width: 2px;
            height: 100%;
            background: linear-gradient(to bottom, #667eea, #764ba2);
        }}

        .timeline-item {{
            display: flex;
            align-items: center;
            margin-bottom: 40px;
            position: relative;
        }}

        .timeline-item:nth-child(odd) {{
            flex-direction: row-reverse;
        }}

        .timeline-content {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            width: 45%;
        }}

        .timeline-dot {{
            width: 20px;
            height: 20px;
            background: #667eea;
            border-radius: 50%;
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            border: 4px solid white;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
        }}

        .code-sample {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 10px;
            overflow-x: auto;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.2);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 30px;
            margin-top: 40px;
        }}

        .stat-card {{
            text-align: center;
            padding: 30px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }}

        .stat-number {{
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }}

        .narration-toggle {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 50px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            cursor: pointer;
            transition: transform 0.3s ease;
            z-index: 1000;
        }}

        .narration-toggle:hover {{
            transform: scale(1.1);
        }}

        @keyframes fadeIn {{
            from {{
                opacity: 0;
            }}
            to {{
                opacity: 1;
            }}
        }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 2.5em;
            }}

            .section {{
                padding: 30px;
            }}

            .timeline-content {{
                width: 85%;
            }}

            .timeline::before {{
                left: 30px;
            }}

            .timeline-dot {{
                left: 30px;
            }}

            .timeline-item {{
                flex-direction: column !important;
                padding-left: 60px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- ヒーローセクション -->
        <div class="hero">
            <h1>🚀 {self.project_name}</h1>
            <p>{project_data.get('description', 'Revolutionary Project Documentation')}</p>
        </div>
"""

        # プロジェクト概要セクション
        html += self._generate_overview_section(project_data)

        # 機能紹介セクション
        html += self._generate_features_section(project_data)

        # 技術スタックセクション
        html += self._generate_tech_stack_section(project_data)

        # スクリーンショットギャラリー
        if screenshots:
            html += self._generate_screenshot_gallery(screenshots)

        # 開発タイムライン
        html += self._generate_timeline_section(project_data)

        # 統計情報
        html += self._generate_stats_section(project_data)

        # ナレーショントグルボタン
        if include_narration:
            html += """
        <div class="narration-toggle" onclick="toggleNarration()">
            🔊 解説を聞く
        </div>
"""

        html += """
    </div>

    <script>
        // スムーズスクロール
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                document.querySelector(this.getAttribute('href')).scrollIntoView({
                    behavior: 'smooth'
                });
            });
        });

        // ナレーション制御
        let narrationAudio = null;

        function toggleNarration() {
            if (narrationAudio && !narrationAudio.paused) {
                narrationAudio.pause();
            } else {
                if (!narrationAudio) {
                    narrationAudio = new Audio('narration.mp3');
                }
                narrationAudio.play();
            }
        }

        // 画像モーダル
        document.querySelectorAll('.screenshot').forEach(img => {
            img.addEventListener('click', function() {
                // 画像拡大表示の実装
                console.log('Image clicked:', this);
            });
        });

        // アニメーショントリガー
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };

        const observer = new IntersectionObserver(function(entries) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);

        document.querySelectorAll('.section').forEach(section => {
            section.style.opacity = '0';
            section.style.transform = 'translateY(20px)';
            section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(section);
        });
    </script>
</body>
</html>
"""

        return html

    def _generate_overview_section(self, data: Dict) -> str:
        """概要セクションを生成"""
        return f"""
        <div class="section">
            <h2>📋 プロジェクト概要</h2>
            <p>{data.get('overview', 'このプロジェクトは革新的なソリューションを提供します。')}</p>
            <div class="feature-grid">
                <div class="feature-card">
                    <div class="icon">🎯</div>
                    <h3>目的</h3>
                    <p>{data.get('purpose', 'ユーザー体験の向上')}</p>
                </div>
                <div class="feature-card">
                    <div class="icon">👥</div>
                    <h3>対象ユーザー</h3>
                    <p>{data.get('target_users', '全てのユーザー')}</p>
                </div>
                <div class="feature-card">
                    <div class="icon">⏱️</div>
                    <h3>開発期間</h3>
                    <p>{data.get('duration', '2週間')}</p>
                </div>
            </div>
        </div>
"""

    def _generate_features_section(self, data: Dict) -> str:
        """機能セクションを生成"""
        features = data.get('features', [])
        if not features:
            features = ['機能1', '機能2', '機能3']

        features_html = """
        <div class="section">
            <h2>✨ 主要機能</h2>
            <div class="feature-grid">
"""

        icons = ['🚀', '⚡', '🔧', '🎨', '📊', '🔒']
        for i, feature in enumerate(features[:6]):
            icon = icons[i % len(icons)]
            features_html += f"""
                <div class="feature-card">
                    <div class="icon">{icon}</div>
                    <h3>{feature if isinstance(feature, str) else feature.get('name', 'Feature')}</h3>
                    <p>{feature.get('description', '') if isinstance(feature, dict) else 'Amazing feature implementation'}</p>
                </div>
"""

        features_html += """
            </div>
        </div>
"""
        return features_html

    def _generate_tech_stack_section(self, data: Dict) -> str:
        """技術スタックセクションを生成"""
        tech_stack = data.get('tech_stack', ['JavaScript', 'Three.js', 'Node.js'])

        tech_html = """
        <div class="section">
            <h2>🛠️ 技術スタック</h2>
            <div class="tech-stack">
"""

        for tech in tech_stack:
            tech_html += f'                <span class="tech-badge">{tech}</span>\n'

        tech_html += """
            </div>
        </div>
"""
        return tech_html

    def _generate_screenshot_gallery(self, screenshots: List[str]) -> str:
        """スクリーンショットギャラリーを生成"""
        gallery_html = """
        <div class="section">
            <h2>📸 スクリーンショット</h2>
            <div class="screenshot-gallery">
"""

        for i, screenshot in enumerate(screenshots):
            gallery_html += f"""
                <div class="screenshot">
                    <img src="{screenshot}" alt="Screenshot {i+1}" />
                </div>
"""

        gallery_html += """
            </div>
        </div>
"""
        return gallery_html

    def _generate_timeline_section(self, data: Dict) -> str:
        """開発タイムラインセクションを生成"""
        milestones = data.get('milestones', [
            {'date': 'Day 1', 'title': 'プロジェクト開始', 'description': '要件定義と設計'},
            {'date': 'Day 3', 'title': '基本実装', 'description': 'コア機能の実装'},
            {'date': 'Day 5', 'title': 'テスト・改善', 'description': 'バグ修正と最適化'},
            {'date': 'Day 7', 'title': 'リリース', 'description': '本番環境へのデプロイ'}
        ])

        timeline_html = """
        <div class="section">
            <h2>📅 開発タイムライン</h2>
            <div class="timeline">
"""

        for milestone in milestones:
            timeline_html += f"""
                <div class="timeline-item">
                    <div class="timeline-content">
                        <h3>{milestone['title']}</h3>
                        <p class="date">{milestone['date']}</p>
                        <p>{milestone['description']}</p>
                    </div>
                    <div class="timeline-dot"></div>
                </div>
"""

        timeline_html += """
            </div>
        </div>
"""
        return timeline_html

    def _generate_stats_section(self, data: Dict) -> str:
        """統計セクションを生成"""
        stats = data.get('stats', {
            'files': 42,
            'lines': 3500,
            'commits': 128,
            'performance': '60 FPS'
        })

        stats_html = """
        <div class="section">
            <h2>📊 プロジェクト統計</h2>
            <div class="stats-grid">
"""

        stat_items = [
            ('ファイル数', stats.get('files', 0), '📁'),
            ('コード行数', stats.get('lines', 0), '💻'),
            ('コミット数', stats.get('commits', 0), '🔄'),
            ('パフォーマンス', stats.get('performance', 'N/A'), '⚡')
        ]

        for label, value, icon in stat_items:
            stats_html += f"""
                <div class="stat-card">
                    <div class="stat-number">{value}</div>
                    <p>{icon} {label}</p>
                </div>
"""

        stats_html += """
            </div>
        </div>
"""
        return stats_html

    def generate_narration_script(self, project_data: Dict) -> str:
        """解説台本を生成"""

        script = f"""# {self.project_name} - 解説台本

## オープニング（0:00 - 0:15）
こんにちは。本日は、{self.project_name}プロジェクトについてご紹介いたします。
このプロジェクトは、{project_data.get('description', '革新的なソリューション')}を実現するために開発されました。

## プロジェクト概要（0:15 - 0:45）
{self.project_name}の主な目的は、{project_data.get('purpose', 'ユーザー体験の向上')}です。
対象となるユーザーは{project_data.get('target_users', '幅広いユーザー層')}で、
約{project_data.get('duration', '2週間')}の開発期間を経て完成しました。

## 主要機能の説明（0:45 - 1:30）
それでは、主要な機能について説明します。
"""

        features = project_data.get('features', [])
        for i, feature in enumerate(features[:3], 1):
            if isinstance(feature, dict):
                script += f"\n第{i}の機能は、{feature.get('name', 'Feature')}です。"
                script += f"これにより、{feature.get('description', 'ユーザーは効率的に作業ができます')}。"
            else:
                script += f"\n第{i}の機能は、{feature}です。"

        script += f"""

## 技術的な実装（1:30 - 2:00）
技術スタックには、{', '.join(project_data.get('tech_stack', ['最新技術']))}を採用しています。
これらの技術を組み合わせることで、高いパフォーマンスと保守性を実現しました。

## パフォーマンスと成果（2:00 - 2:30）
プロジェクトの成果として、以下の数値を達成しました：
- コード行数: {project_data.get('stats', {}).get('lines', '約3000')}行
- パフォーマンス: {project_data.get('stats', {}).get('performance', '60FPS')}
- 開発効率: 計画通りの期間で完成

## まとめ（2:30 - 2:45）
以上が{self.project_name}プロジェクトの概要です。
このプロジェクトは、ユーザーに新しい価値を提供し、
今後もさらなる改善を続けていく予定です。

ご清聴ありがとうございました。

---

## 読み上げ用マーカー
<!-- TTS設定: 速度=1.0, ピッチ=1.0, 音声=ja-JP-Wavenet-B -->
<!-- 各セクションで0.5秒のポーズ -->
<!-- 重要な数値は強調して読む -->
"""

        return script

    def generate_tts_config(self) -> Dict:
        """Google TTS API用の設定を生成"""

        config = {
            "voice": {
                "languageCode": "ja-JP",
                "name": "ja-JP-Wavenet-B",  # 男性の声
                # "name": "ja-JP-Wavenet-A",  # 女性の声（選択可能）
                "ssmlGender": "MALE"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.0,  # 話す速度（0.25-4.0）
                "pitch": 0.0,  # ピッチ（-20.0-20.0）
                "volumeGainDb": 0.0,  # 音量（-96.0-16.0）
                "effectsProfileId": ["headphone-class-device"]  # オーディオプロファイル
            }
        }

        return config

    def prepare_ssml_text(self, script: str) -> str:
        """台本をSSML形式に変換"""

        # セクションの区切りでポーズを入れる
        ssml_text = script.replace('\n\n', '<break time="1s"/>\n\n')

        # 数値を強調
        ssml_text = re.sub(r'(\d+)', r'<emphasis level="moderate">\1</emphasis>', ssml_text)

        # 重要な単語を強調
        important_words = ['主要', '重要', '革新的', '成功', '完成']
        for word in important_words:
            ssml_text = ssml_text.replace(word, f'<emphasis level="strong">{word}</emphasis>')

        # SSML タグでラップ
        ssml = f"""<speak>
{ssml_text}
</speak>"""

        return ssml

    def save_documentation(self,
                          html_content: str,
                          script_content: str,
                          output_dir: str = "./docs") -> Dict:
        """生成したドキュメントを保存"""

        os.makedirs(output_dir, exist_ok=True)

        # HTMLファイルを保存
        html_path = os.path.join(output_dir, "project_presentation.html")
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # 台本を保存
        script_path = os.path.join(output_dir, "narration_script.md")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        # SSML形式の台本も保存
        ssml_content = self.prepare_ssml_text(script_content)
        ssml_path = os.path.join(output_dir, "narration_script.ssml")
        with open(ssml_path, 'w', encoding='utf-8') as f:
            f.write(ssml_content)

        # TTS設定を保存
        tts_config = self.generate_tts_config()
        tts_config_path = os.path.join(output_dir, "tts_config.json")
        with open(tts_config_path, 'w', encoding='utf-8') as f:
            json.dump(tts_config, f, ensure_ascii=False, indent=2)

        return {
            "html": html_path,
            "script": script_path,
            "ssml": ssml_path,
            "tts_config": tts_config_path
        }