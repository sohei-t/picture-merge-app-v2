# 📌 ワークフロー チェックポイント システム

## 🎯 目的

エージェントがタスクを忘れずに、確実にすべてのステップを実行するための仕組み

## 🔴 最重要ルール

**各フェーズ開始時に必ずチェックポイント確認を出力すること**

```
=================================
📌 チェックポイント: フェーズ5 - 完成処理
=================================
実行すべきタスク:
✅ README.md 生成
✅ about.html 生成（必須）
✅ explanation.mp3 生成（必須）
✅ launch_app.command 生成
=================================
```

## 📊 フェーズ別チェックリスト

### フェーズ1: 計画
```yaml
checkpoint_1:
  name: "計画フェーズ"
  required_outputs:
    - REQUIREMENTS.md
    - WBS.json
    - tests/*.test.js または tests/*.py
  validation:
    - "要件が明確に定義されているか"
    - "WBSが詳細に分解されているか"
    - "テストが先に作成されているか"
```

### フェーズ2: 実装
```yaml
checkpoint_2:
  name: "実装フェーズ"
  required_outputs:
    - src/* (ソースコード)
    - package.json または requirements.txt
  validation:
    - "フロントエンドが実装されているか"
    - "バックエンドが実装されているか"
    - "依存関係が定義されているか"
```

### フェーズ3: テスト合格（必須・回数制限なし）
```yaml
checkpoint_3:
  name: "テスト合格フェーズ"
  required_outputs:
    - テスト実行ログ
    - 修正されたソースコード
    - カバレッジレポート
  validation:
    - "作成済みテストが100%合格しているか"
    - "カバレッジ70%以上を達成しているか"
    - "クリティカルパス（認証、決済、データ検証）が100%カバーされているか"
    - "エラーがすべて解決されているか"
  重要:
    - "作成済みテストの100%合格は必須要件"
    - "修正は合格まで継続（回数制限なし）"
    - "次フェーズへ進む前提条件"
```

### フェーズ4: 品質改善（任意・最大3回）
```yaml
checkpoint_4:
  name: "品質改善フェーズ"
  required_outputs:
    - EVALUATION_REPORT.md
    - IMPROVEMENT_PLAN.md（必要な場合）
    - 改善されたコード
    - 更新されたカバレッジレポート
  validation:
    - "カバレッジ80-90%を達成しているか"
    - "ビジネスロジック: 90-100%カバレッジ"
    - "API/統合: 80-90%カバレッジ"
    - "UI/E2E: 70-80%カバレッジ"
    - "パフォーマンスが基準を満たしているか"
    - "コードの可読性が高いか"
    - "セキュリティ問題がないか"
  注意:
    - "これは任意の改善"
    - "最大3回の改善ループ"
    - "作成済みテストは既に100%合格済みが前提"
```

### フェーズ5: 完成処理（最重要）
```yaml
checkpoint_5:
  name: "完成処理フェーズ"
  required_outputs:
    - README.md
    - about.html（Webアプリ/ゲーム必須）
    - audio_script.txt（必須）
    - explanation.mp3（Gemini TTS優先、GCPフォールバック）
    - launch_app.command（必須）
  validation:
    - "README.md が生成されているか"
    - "about.html が存在するか"
    - "音声ファイルが生成されているか（または理由が記録されているか）"
    - "起動スクリプトが実行可能か"
  音声生成:
    優先順位:
      1. "Gemini 2.5 Flash Preview TTS（GEMINI_API_KEY設定時）"
      2. "GCP Text-to-Speech（GCP認証ファイル存在時）"
      3. "スキップ（両方失敗時、理由をREADME.mdに記録）"
  special_commands:
    - "python3 ~/Desktop/git-worktree-agent/_workflow/src/documenter_agent.py"
    - "chmod +x launch_app.command"
```

## 🔄 実行確認プロセス

### ステップ1: チェックポイント表示
```python
def show_checkpoint(phase, tasks):
    print("="*50)
    print(f"📌 チェックポイント: {phase}")
    print("="*50)
    print("実行すべきタスク:")
    for task in tasks:
        print(f"  ✅ {task}")
    print("="*50)
```

### ステップ2: 実行状況の記録
```python
def record_execution(task, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("WORKFLOW_LOG.md", "a") as f:
        f.write(f"- [{timestamp}] {task}: {status}\n")
```

### ステップ3: 完了確認
```python
def verify_completion(required_files):
    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if missing:
        print(f"⚠️  未生成ファイル: {missing}")
        return False

    print("✅ すべてのファイルが生成されました")
    return True
```

## 📝 エージェントへの指示テンプレート

### Documenter エージェント用の明確な指示

```markdown
【重要】以下の手順を必ず実行してください：

1. README.md を生成
   - プロジェクト概要
   - インストール手順
   - 使用方法

2. about.html を生成（必須）
   - documenter_agent.py を実行:
   ```bash
   python3 ~/Desktop/git-worktree-agent/_workflow/src/documenter_agent.py
   ```

3. 音声スクリプト作成（必須）
   - audio_script.txt が生成される
   - SSML不要（Gemini TTSは自然言語で間を認識）

4. 音声生成（自動実行）
   documenter_agent.py が以下の優先順位で試行:
   1. Gemini 2.5 Flash Preview TTS（GEMINI_API_KEY設定時、推奨）
   2. GCP Text-to-Speech（GCP認証ファイル存在時、フォールバック）
   3. スキップ（両方失敗時、理由をREADME.mdに記録）

5. 生成確認
   ```bash
   ls -la about.html audio_script.txt explanation.mp3
   ```

【失敗しないためのチェック】
- about.html が存在すること
- audio_script.txt が存在すること
- explanation.mp3 が存在すること（または理由が記録されていること）
```

## 🚨 忘れやすいポイントと対策

### 問題1: about.html が生成されない
**原因**: Documenter が README.md だけ作って終了
**対策**: 明示的に documenter_agent.py の実行を指示

### 問題2: 音声ファイルが作成されない
**原因**: 認証情報が設定されていない
**対策**:
1. Gemini TTS: `GEMINI_API_KEY` を `~/.config/ai-agents/profiles/default.env` に設定
2. GCP TTS: `~/.config/ai-agents/credentials/gcp/default.json` に認証ファイル配置
3. セットアップガイド: `GCP_TTS_SETUP.md` を参照

### 問題3: launch_app.command が実行できない
**原因**: chmod +x を忘れる
**対策**: 生成後に必ず chmod +x を実行

## 🎯 改善された Documenter 実行フロー

```bash
# 1. Pythonスクリプトで自動生成（音声も自動生成）
cd worktrees/mission-*/
python3 ~/Desktop/git-worktree-agent/_workflow/src/documenter_agent.py

# 2. 生成物の確認
echo "📄 生成されたドキュメント:"
ls -la about.html audio_script.txt explanation.mp3 2>/dev/null || echo "⚠️ ファイルが見つかりません"

# 3. 音声生成状況の確認
if [ -f "explanation.mp3" ]; then
  echo "✅ 音声ファイル生成完了"
else
  echo "⚠️ 音声ファイル未生成（認証情報を確認してください）"
  echo "  - Gemini TTS: GEMINI_API_KEY を設定"
  echo "  - GCP TTS: ~/.config/ai-agents/credentials/gcp/default.json を配置"
fi

# 4. 成功メッセージ
echo "✅ ドキュメント生成フェーズ完了"
```

## 📊 ワークフローログの例

```markdown
# WORKFLOW_LOG.md

## プロジェクト: TodoApp
## 開始: 2024-12-09 10:00:00

### フェーズ1: 計画
- [2024-12-09 10:00:15] Requirements Analysis: ✅ 完了
- [2024-12-09 10:05:30] WBS Creation: ✅ 完了
- [2024-12-09 10:10:45] Test Design: ✅ 完了

### フェーズ2: 実装
- [2024-12-09 10:15:00] Frontend Development: ✅ 完了
- [2024-12-09 10:15:00] Backend Development: ✅ 完了
- [2024-12-09 10:25:00] Database Setup: ✅ 完了

### フェーズ3: テスト
- [2024-12-09 10:30:00] Test Execution: ❌ 失敗 (5/10)
- [2024-12-09 10:35:00] Bug Fix: ✅ 完了
- [2024-12-09 10:40:00] Test Re-execution: ✅ 合格 (10/10)

### フェーズ4: 品質改善
- [2024-12-09 10:45:00] Quality Evaluation: ✅ 完了
- [2024-12-09 10:50:00] Performance Optimization: ✅ 完了

### フェーズ5: 完成処理
- [2024-12-09 10:55:00] README.md Generation: ✅ 完了
- [2024-12-09 10:56:00] about.html Generation: ✅ 完了
- [2024-12-09 10:57:00] Audio Script Creation: ✅ 完了
- [2024-12-09 10:58:00] launch_app.command: ✅ 完了

## 完了: 2024-12-09 11:00:00
```

## 🎯 これで解決される問題

1. **タスクの抜け漏れ防止**
   - チェックポイントで必須タスクを明示
   - 実行ログで履歴を追跡

2. **about.html と音声生成の確実な実行**
   - documenter_agent.py の明示的な実行
   - 生成物の存在確認

3. **エージェントの記憶保持**
   - 各フェーズでワークフロー再確認
   - チェックリストによる確認

4. **問題の早期発見**
   - 各フェーズ終了時の検証
   - 未生成ファイルの警告