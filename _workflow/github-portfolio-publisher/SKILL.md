---
name: github-portfolio-publisher
description: Publishes DELIVERY folder contents to sohei-t/ai-agent-portfolio repository following strict rules for portfolio management and code updates.
---

# GitHub Portfolio Publisher

DELIVERYフォルダの内容のみを https://github.com/sohei-t/ai-agent-portfolio の適切なフォルダに公開・更新するスキル。

## Essential Requirements

### 公開ルール
1. **DELIVERYフォルダのみ**: worktreesやソースコード全体は公開しない
2. **固定リポジトリ**: 必ず `sohei-t/ai-agent-portfolio` に公開
3. **フォルダ構造**: リポジトリ直下の `/{app-name}/` に配置
4. **更新時**: 既存フォルダを上書き

### 必須ファイル（DELIVERY内）
- `index.html` - アプリのエントリポイント（ビルド済みのものを使用）
- `README.md` - アプリの説明
- `about.html` - ビジュアル説明ページ（mp3埋め込み）
- `assets/` - 画像/音声/JS/CSS など公開に必要な静的ファイル
- `explanation.mp3` - 音声解説
- `dist/` - ビルド成果物が必要な場合のみ（相対参照で動作確認済み）

## Usage Commands

### 初回公開／更新（統一）
```bash
# DELIVERYフォルダ作成
python3 src/delivery_organizer.py

# GitHub公開（専用環境のmainで、公開物のみ）
python3 src/simplified_github_publisher.py .
```

## Workflow Patterns

### パターン: 修正後の再公開
```bash
# 開発はworktreeで行い、mainにマージ後、専用環境mainで実行
python3 src/delivery_organizer.py
python3 src/simplified_github_publisher.py .
```

## Common Mistakes to Avoid

1. **worktrees全体を公開**: DELIVERYフォルダのみ（.env/credentials/node_modules/プロンプト等は除外）
2. **違うリポジトリに公開**: 必ず sohei-t/ai-agent-portfolio を使用
3. **テスト未実行**: 公開前に必ずテストを実行
4. **DELIVERY未作成**: delivery_organizer.py を必ず実行
5. **不要ファイル同梱**: 公開前に内容確認してから simplified_github_publisher.py を実行

## File Locations

```
project-root/
├── src/
│   ├── delivery_organizer.py     # DELIVERY作成
│   ├── simplified_github_publisher.py    # GitHub公開
│   └── documenter_agent_v2.py    # ドキュメント生成
├── worktrees/
│   └── mission-v1/
│       └── DELIVERY/              # 公開対象
├── update_and_publish.sh         # 自動更新スクリプト
└── CODE_UPDATE_WORKFLOW.md        # ワークフロー説明
```

## Verification Checklist

公開前に確認:
- [ ] DELIVERYフォルダが存在
- [ ] index.html, README.md, about.html が含まれる
- [ ] 必要なビルド成果物（assets/, dist/など）が含まれる
- [ ] テストが全てパス
- [ ] 不要ファイルが除外されている（.env/credentials/node_modules/プロンプト/テストコード等）
- [ ] リポジトリURLが正しい (sohei-t/ai-agent-portfolio)

## Error Recovery

### DELIVERYフォルダが見つからない
```bash
python3 src/delivery_organizer.py
```

### Git push失敗
```bash
cd ~/Desktop/GitHub/ai-agent-portfolio
git pull origin main --rebase
# 再度実行
python3 src/simplified_github_publisher.py .
```

### テスト失敗
```bash
# 修正後、再度テスト
npm test
# または
python3 -m pytest
```

## URLs and Access

- **GitHub**: https://github.com/sohei-t/ai-agent-portfolio
- **GitHub Pages**: https://sohei-t.github.io/ai-agent-portfolio/
- **App URL Pattern**: https://sohei-t.github.io/ai-agent-portfolio/{app-name}/

## Important Notes

1. **セキュリティ**: DELIVERYフォルダ以外のコードは絶対に公開しない
2. **バージョン管理**: 大きな変更は新しいブランチで作業
3. **テスト必須**: エラーがある状態では公開しない
4. **定期確認**: GitHub Pagesの動作を確認
