# 🎯 API利用ポリシー v2.0

## 基本方針

**原則: $0（ゼロコスト）を最優先、ただし価値向上のための低コストAPIは自動承認**

すべてのアプリは、外部有料APIなしで動作することを前提とする。
ただし、ポートフォリオの価値を高めるため、以下の低コストAPIは自動的に利用する。

---

## 🟢 自動承認API（認証ファイル存在時）

### 1. 音声生成（Gemini TTS → GCP TTSフォールバック）

**推奨: Gemini 2.5 Flash Preview TTS**
- `GEMINI_API_KEY` 環境変数が設定されている場合
- APIキーのみで利用可能（サービスアカウント不要）
- SSML不要（自然言語で間を認識）
- 高品質な日本語音声

**フォールバック: GCP Text-to-Speech**
- `~/.config/ai-agents/credentials/gcp/default.json` が存在する場合
- Gemini TTS失敗時に自動的にフォールバック

**コスト:**
- Gemini TTS: 無料枠あり
- GCP TTS: 月間100万文字無料（WaveNet）
- 想定使用量: 月1000プロジェクト → **完全に無料枠内**

**実行タイミング:**
- Phase 5: 完成処理フェーズ
- documenter_agent.py が自動実行

**フォールバック:**
- Gemini TTS失敗 → GCP TTS試行
- 両方失敗時: 音声なしで継続（理由をREADME.mdに記録）

**価値:**
- ✅ ポートフォリオの差別化
- ✅ アクセシビリティ向上
- ✅ プロフェッショナル感の演出

---

### 2. Vertex AI Imagen（AI画像生成）

**自動実行条件:**
- 画像生成が必要なプロジェクト（ゲーム等）
- 認証ファイルが存在 OR 自動セットアップ成功
- ユーザーが「AI画像生成」を明示的に要求 OR デフォルト有効化

**コスト:**
- 1画像: $0.020
- 1ゲーム: 20-30画像 → **$0.40-0.60**
- 月間50ゲーム: **$20-30**

**実行タイミング:**
- Phase 2: 実装フェーズ
- 画像アセット生成時

**フォールバック:**
- Imagen失敗時: SVG/Canvas代替（カラフル図形）
- 認証なし時: 同上

**価値:**
- ✅ AI技術のアピール
- ✅ 高品質なビジュアル
- ✅ 開発時間の大幅短縮

**新方針（v2.0）:**
- **デフォルトでImagen生成を試行**
- 失敗時のみSVG代替
- コスト管理: 月間予算$25を推奨

---

## 🟡 明示的承認が必要なAPI

### 1. Cloud SQL / Cloud Firestore

**条件:**
- ユーザーが「Cloud SQL」「Firestore」を明示的に要求
- 確認プロンプト表示: 「この機能は月額$XX かかります。続行しますか？」

**デフォルト:**
- SQLite（ローカル）

**コスト:**
- Cloud SQL: 月額$7-25
- Firestore: 従量課金（無料枠あり）

---

### 2. その他の有料API

**条件:**
- ユーザーが明示的に要求
- コスト試算を提示して承認を得る

**デフォルト:**
- 無料代替を優先

---

## 🚦 判定フローチャート

```
ユーザーリクエスト受信
  ↓
画像生成が必要？
  ├─ YES → 画像生成判定へ
  └─ NO → 次へ

音声解説が必要？（Phase 5）
  ├─ YES → TTS自動実行
  └─ NO → スキップ

「Cloud SQL」「Firebase」等のキーワードあり？
  ├─ YES → ユーザーに確認
  │         「この機能は月額$XX かかります。続行しますか？」
  │         ├─ 承認 → 高コストAPI使用
  │         └─ 拒否 → SQLite等の代替
  └─ NO → デフォルトポリシー（$0実装）
```

---

## 🎨 画像生成判定フロー（新設）

```
画像アセットが必要か？
  ↓
YES → Imagen自動実行フロー
  ↓
認証ファイル確認
  ├─ 存在 → Imagen API実行
  │         ├─ 成功 → AI生成画像を使用
  │         └─ 失敗（クォータ超過等）→ SVG代替
  └─ 不存在 → 自動セットアップ試行
            ├─ 成功 → Imagen API実行
            └─ 失敗 → SVG代替

SVG代替:
  - カラフルな幾何学図形
  - Canvas動的生成
  - フリー素材（OpenGameArt等）
```

---

## 📝 サブエージェントへの指示

各サブエージェントプロンプトに以下を追加：

### Phase 2（実装フェーズ）

```yaml
【画像生成の自動判定】
1. このタスクで画像アセットが必要か確認
2. 必要な場合:
   ⚠️ use the gcp skill を明示的に宣言
   - Vertex AI Imagen API セットアップスクリプト実行
     (./.claude/skills/gcp-skill/IMAGEN_API.md 参照)
   - 画像生成プロンプトを英語で作成
   - generate_image() 実行
   - 失敗時: SVG代替を自動生成
3. 不要な場合: スキップ

【重要】
- 画像生成は「価値向上」のため推奨
- コスト: 1ゲーム約$0.50（月間予算$25推奨）
- 失敗時のフォールバックは必須
```

### Phase 5（完成処理フェーズ）

```yaml
【音声生成の自動実行】
documenter_agent.py が自動的に以下を試行:

優先順位:
  1. Gemini 2.5 Flash Preview TTS（GEMINI_API_KEY設定時）
  2. GCP Text-to-Speech（GCP認証ファイル存在時）
  3. スキップ（両方失敗時、理由をREADME.mdに記録）

セットアップ:
  - Gemini TTS: GEMINI_API_KEY を ~/.config/ai-agents/profiles/default.env に設定
  - GCP TTS: ~/.config/ai-agents/credentials/gcp/default.json に認証ファイル配置

【重要】
- 音声は「差別化」のため推奨
- コスト: 無料枠内（月1000プロジェクト）
- 失敗してもワークフロー停止しない
```

---

## 🔧 認証ファイルの自動セットアップ

### 統合サービスアカウント（推奨）

TTS + Imagen を1つのサービスアカウントで管理：

```bash
# サービスアカウント名: ai-agent
# 権限:
#   - roles/cloudtts.admin (Text-to-Speech)
#   - roles/aiplatform.user (Vertex AI Imagen)

# 認証ファイル: $GOOGLE_APPLICATION_CREDENTIALS
# ※ 名前は"tts"だが、実際はTTS+Imagen両方に使用
```

### セットアップ手順

**Phase 5（TTS）:**
```bash
# CLAUDE.md 音声生成用プロンプト参照
# サービスアカウント作成 + TTS権限付与
```

**Phase 2（Imagen追加）:**
```bash
# gcp-skill/IMAGEN_API.md 参照
# 既存のサービスアカウントにVertex AI権限を追加
```

---

## 💰 月間コスト試算

### 標準的な使用量

| 項目 | 単価 | 数量 | 月間コスト |
|------|------|------|----------|
| **Text-to-Speech** | 無料 | 1000プロジェクト | **$0** |
| **Vertex AI Imagen** | $0.50/ゲーム | 50ゲーム | **$25** |
| **合計** | - | - | **$25/月** |

### 無料トライアル活用

- GCP無料クレジット: $300（90日間）
- 600ゲーム分のImagen生成可能
- TTS: 完全無料枠内

### 予算上限設定

```bash
# 月間$25上限（推奨）
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="AI Agent Monthly Budget" \
  --budget-amount=25USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

---

## 🎯 ポリシー変更履歴

### v2.0（2025-01-XX）
- ✅ Imagen APIを「自動承認」に変更
- ✅ デフォルトでAI画像生成を試行
- ✅ 月間予算$25を推奨
- ✅ 統合サービスアカウント方式を採用

### v1.0（2024-12-XX）
- $0優先ポリシー
- TTS: 自動承認
- Imagen: 明示的承認必要

---

## 📊 ポリシー適用例

### 例1: モバイルゲーム開発

```
リクエスト: "シューティングゲームを作って"

判定:
  - 画像必要: YES → Imagen自動実行
  - 音声必要: YES → TTS自動実行（Phase 5）

結果:
  - プレイヤー・敵・弾丸: AI生成（$0.50）
  - explanation.mp3: AI生成（無料）
  - 合計コスト: $0.50
```

### 例2: Webアプリ開発

```
リクエスト: "Todoアプリを作って"

判定:
  - 画像必要: NO → スキップ
  - 音声必要: YES → TTS自動実行

結果:
  - 画像: なし
  - explanation.mp3: AI生成（無料）
  - 合計コスト: $0
```

### 例3: 外部API要求

```
リクエスト: "Cloud SQLを使ったCRMシステムを作って"

判定:
  - "Cloud SQL"キーワード検出 → ユーザー確認

確認プロンプト:
  "Cloud SQLは月額約$15かかります。続行しますか？
   代替案: SQLite（無料）"

  [承認] → Cloud SQL使用
  [拒否] → SQLite使用
```

---

## ✅ チェックリスト

### 初回セットアップ
- [ ] GCPプロジェクト設定（`gcloud config set project`）
- [ ] 課金アカウント有効化（無料トライアル可）
- [ ] 予算アラート設定（$25推奨）

### ワークフロー実行前
- [ ] DEFAULT_POLICY.md 確認
- [ ] API_USAGE_POLICY.md 確認（このファイル）
- [ ] 月間予算残高確認

### 各フェーズ実行時
- [ ] Phase 2: 画像生成判定 → Imagen試行 → フォールバック
- [ ] Phase 5: 音声生成自動実行 → explanation.mp3生成

---

## 🆘 トラブルシューティング

### Q1: Imagen生成が毎回失敗する

```bash
# 原因確認
gcloud services list --enabled | grep aiplatform

# API有効化
gcloud services enable aiplatform.googleapis.com

# 権限確認
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:ai-agent"
```

### Q2: コストが予算を超えそう

```bash
# 使用量確認
gcloud billing budgets list

# Imagen一時停止
# → CLAUDE.md Phase 2 の画像生成判定を手動でスキップ設定
```

### Q3: 認証ファイルが見つからない

```bash
# 確認
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# 再生成（TTS用）
# → CLAUDE.md 音声生成用プロンプト参照

# Imagen権限追加
# → gcp-skill/IMAGEN_API.md 参照
```

---

## 📚 関連ドキュメント

- [CLAUDE.md](./CLAUDE.md) - ワークフロー定義
- [DEFAULT_POLICY.md](./DEFAULT_POLICY.md) - デフォルトポリシー
- [GCP_TTS_SETUP.md](./GCP_TTS_SETUP.md) - TTS設定ガイド
- [IMAGEN_QUOTA_GUIDE.md](./IMAGEN_QUOTA_GUIDE.md) - Imagenクォータ管理
- [gcp-skill/IMAGEN_API.md](./.claude/skills/gcp-skill/IMAGEN_API.md) - Imagen実装ガイド

---

**このポリシーにより、音声・画像の両方を自動生成し、ポートフォリオの価値を最大化します。**
