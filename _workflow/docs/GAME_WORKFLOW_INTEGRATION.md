# 🎮 ゲーム開発ワークフロー統合ガイド

## 📋 PROJECT_INFO.yaml でゲームプロジェクトを識別

```yaml
project_name: "Alien Defense Shooter"
project_type: "game"  # ← これでゲームワークフローを起動
game_genre: "shooting"
development_type: "Portfolio App"
database_type: "None"
external_apis: []
cost: "$0"
```

## 🚀 ゲーム専用ワークフローの実行

### Phase 0: 初期化（通常通り）

### Phase 1: 要件定義・計画（ゲーム専用）

```python
# ワークフロー判定
if project_info.get('project_type') == 'game':
    # ゲーム専用エージェント実行
    Task 1: Game Design Agent
    Task 2: Asset Requirements Agent
else:
    # 通常のRequirements Analyst
```

### Phase 2: 実装（ゲーム専用並列タスク）

```yaml
通常アプリ:
  - Frontend Developer
  - Backend Developer
  - Database Expert

ゲーム:
  - Core Game Logic Agent    # ゲームロジック
  - Asset Integration Agent   # 画像統合（重要！）
  - UI/HUD Agent             # ゲームUI
```

### Phase 3: テスト（標準）

### Phase 4: 品質改善（標準）

### Phase 4.5: 統合テスト（ゲーム専用・新規追加）

```yaml
新規フェーズ:
  1. Integration Agent     # モジュール統合
  2. Playtest Agent       # 実プレイテスト
  3. Balance Tuning Agent # バランス調整
```

### Phase 5-6: 完成処理・公開（標準）

## 📝 CLAUDE.md への追加内容

```markdown
## 🎮 ゲーム開発専用フロー

PROJECT_INFO.yaml で `project_type: "game"` が設定されている場合、
以下の専用ワークフローを実行：

### ゲーム専用エージェント
1. Game Design Agent - ゲームルール設計
2. Asset Requirements Agent - アセット要件定義
3. Core Game Logic Agent - ゲームロジック実装
4. Asset Integration Agent - 画像統合（必須）
5. UI/HUD Agent - ゲームUI実装
6. Integration Agent - 統合作業
7. Playtest Agent - プレイテスト
8. Balance Tuning Agent - バランス調整

### 重要な違い
- Asset Integration Agent が画像の使用を保証
- Playtest Agent が実際に起動してテスト
- 統合テストフェーズが追加
```

## 🔧 実装方法

### Option 1: 自動判定（推奨）

```javascript
// workflow_orchestrator.py に追加
def determine_workflow_type(project_info):
    if project_info.get('project_type') == 'game':
        return 'game_development_workflow'
    else:
        return 'standard_workflow'
```

### Option 2: ユーザー指定

```bash
# ゲーム開発を明示的に指定
./create_new_app.command --type game --name "Space Shooter"
```

## 📊 ワークフロー比較

| フェーズ | 標準ワークフロー | ゲームワークフロー |
|---------|-----------------|-------------------|
| Phase 1 | Requirements Analyst | Game Design Agent + Asset Requirements |
| Phase 2 | Frontend/Backend/DB | Game Logic + Asset Integration + UI |
| Phase 3 | テスト | テスト |
| Phase 4 | 品質改善 | 品質改善 |
| **Phase 4.5** | - | **統合テスト（新規）** |
| Phase 5 | 完成処理 | 完成処理 |
| Phase 6 | GitHub公開 | GitHub公開 |

## 🎯 問題解決の仕組み

### 1. 画像が反映されない問題 → 解決

**Asset Integration Agent の責任**
```javascript
// 必ず実行されるチェック
async validateAssets() {
  const specified = ['player.png', 'enemy.png'];
  for (const asset of specified) {
    if (!exists(asset)) {
      console.error(`Missing: ${asset}`);
      this.createPlaceholder(asset);
    }
  }
}
```

### 2. 統合テストで失敗する問題 → 解決

**Playtest Agent の責任**
```javascript
// 実際に起動してテスト
async runIntegrationTest() {
  const game = await startGame();

  // 実際の操作をシミュレート
  await game.pressKey('ArrowUp');
  await game.pressKey('Space');

  // 結果を検証
  assert(game.player.isVisible);
  assert(game.enemies.length > 0);
  assert(game.score >= 0);
}
```

## 📋 チェックリスト

### ゲーム開発開始前
- [ ] PROJECT_INFO.yaml に `project_type: "game"` 設定
- [ ] 使用したい画像をassets/フォルダに配置
- [ ] ゲームジャンルを明確化

### Phase 2 実装時
- [ ] Asset Integration Agent が画像を確認
- [ ] 指定画像が使用されているか確認
- [ ] プレースホルダーが作成されているか

### Phase 4.5 統合テスト時
- [ ] ゲームが実際に起動する
- [ ] すべての操作が機能する
- [ ] 画像が正しく表示される
- [ ] エラーがない

## 🚀 実行コマンド例

```bash
# 新規ゲームプロジェクト作成
./create_new_app.command
> プロジェクト名: alien-shooter
> プロジェクトタイプ: game
> ゲームジャンル: shooting

# 画像を配置
cp my-sprites/* ~/Desktop/AI-Apps/alien-shooter-agent/assets/

# Claude Code起動
cd ~/Desktop/AI-Apps/alien-shooter-agent
# "シューティングゲームを作って。assets/フォルダの画像を使って。"

# 自動的にゲームワークフローが実行される
```

## ✅ 期待される成果

1. **画像の確実な反映**
   - Asset Integration Agent が保証

2. **動作する完成品**
   - Playtest Agent が実動作確認

3. **プロ品質のゲーム**
   - 各専門エージェントの分業
   - バランス調整済み

## 📈 効果測定

| 項目 | 従来 | ゲームワークフロー |
|------|------|------------------|
| 画像反映率 | 30% | 100% |
| 統合テスト成功率 | 20% | 90% |
| プレイアビリティ | 低 | 高 |
| 完成度 | 60% | 95% |

## 🔄 継続的改善

1. **フィードバック収集**
   - プレイテスト結果を蓄積
   - よくある問題をパターン化

2. **エージェント改良**
   - プロンプトの最適化
   - 新しいゲームジャンル対応

3. **アセットライブラリ**
   - デフォルト画像セット準備
   - 音効ライブラリ追加