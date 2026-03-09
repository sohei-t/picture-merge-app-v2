# 公開ファイル格納フォルダ（自動生成）
このフォルダにはGitHub公開用のファイルが格納されます。

## フォルダ構成:
- public/ - GitHub公開用ファイル（Phase 5で documenter_agent.py が自動生成）
  - index.html - アプリ本体
  - about.html - プロジェクト紹介ページ
  - assets/ - 静的ファイル（CSS/JS/画像など）
  - README.md - 公開用概要
  - explanation.mp3 - 音声解説（オプション）

## ワークフロー:
1. Phase 5: documenter_agent.py が public/ 配下にファイル生成
2. Phase 6: simplified_github_publisher.py が public/ を読み取ってGitHub公開

詳細: ../CLAUDE.md の Phase 5 および Phase 6 を参照
