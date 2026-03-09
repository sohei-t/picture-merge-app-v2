# 🎯 デフォルトポリシー（最優先原則）

## 📋 基本原則

**全自動化とゼロコストを最優先とし、明示的な要求がある場合のみ外部サービスを使用する**

## 🚀 デフォルトポリシー（通常適用）

### 1. 開発方針
```yaml
default_policy:
  automation: "100%全自動"
  cost: "$0（完全無料）"
  deployment: "ローカル実行"
  external_apis: "使用しない"
  database: "SQLite/LocalStorage"
  authentication: "ローカル認証"
  hosting: "なし（launch_app.command）"
```

### 2. 技術選択の優先順位

#### データベース
```yaml
priority_order:
  1_local:
    - SQLite（ファイルベース）
    - LocalStorage（ブラウザ）
    - JSON ファイル
    cost: "$0"
    complexity: "低"

  2_only_if_requested:
    - Cloud SQL
    - Firestore
    - MongoDB Atlas
    cost: "$10-100+/月"
    trigger: "明示的な要求時のみ"
```

#### ホスティング
```yaml
priority_order:
  1_local:
    - launch_app.command（ローカル起動）
    - Python SimpleHTTPServer
    - Node.js Express（ローカル）
    cost: "$0"

  2_free_tier:
    - GitHub Pages（静的サイト）
    - Vercel（無料枠）
    - Netlify（無料枠）
    cost: "$0"

  3_only_if_requested:
    - Cloud Run
    - App Engine
    - AWS/Azure
    cost: "$10+/月"
```

#### 外部API
```yaml
priority_order:
  1_avoid:
    default: "外部APIを使わない実装"
    alternative: "モック/ローカル実装"

  2_only_if_requested:
    condition: "ユーザーが明示的に要求"
    examples:
      - "Vertex AIを使いたい"
      - "LINEボットを作りたい"
      - "OpenAI APIを統合したい"
```

## 🔄 判定フロー

### ステップ1: 要件分析
```python
def analyze_requirements(user_request):
    # 明示的な外部サービス要求をチェック
    external_services = detect_external_requirements(user_request)

    if not external_services:
        # デフォルトポリシー適用
        return apply_default_policy()
    else:
        # 外部サービス対応フロー
        return apply_external_api_workflow(external_services)

def detect_external_requirements(request):
    """明示的な要求のみを検出"""
    explicit_keywords = [
        "Cloud SQL", "Vertex AI", "LINE", "OpenAI",
        "Cloud Run", "GCP", "AWS", "Azure",
        "Stripe", "SendGrid", "Firebase"
    ]

    detected = []
    for keyword in explicit_keywords:
        if keyword.lower() in request.lower():
            detected.append(keyword)

    return detected
```

### ステップ2: 提案生成
```yaml
proposal_generation:
  case_1_default:
    trigger: "外部サービス要求なし"
    proposal: |
      【提案】ローカル完結型の実装
      - コスト: $0
      - 実行: launch_app.command
      - DB: SQLite
      - 全自動開発（人間の介入不要）

  case_2_hybrid:
    trigger: "一部外部サービス要求あり"
    proposal: |
      【提案】最小限の外部サービス利用
      - ローカル開発 + 必要な部分のみ外部
      - 段階的移行可能な設計
      - コスト最小化

  case_3_full_external:
    trigger: "本格的な外部サービス要求"
    proposal: |
      【確認】外部サービスを利用します
      - 月額コスト: $XXX
      - 必要な作業: 30分
      - APIキー設定が必要
      承認しますか？(y/n)
```

## 📊 実装例

### ケース1: 通常のTodoアプリ要求
```markdown
User: "Todoアプリを作って"

AI判定: 外部サービス要求なし → デフォルトポリシー適用

AI応答:
「Todoアプリを全自動で開発します。
- DB: SQLite（ローカル）
- 起動: launch_app.command
- コスト: $0
すぐに開発を開始します。」

→ 従来通り全自動開発
```

### ケース2: 明示的なDB要求
```markdown
User: "Cloud SQLを使ったTodoアプリを作って"

AI判定: 明示的な外部サービス要求あり → 確認フロー

AI応答:
「Cloud SQLを使用したTodoアプリですね。
【確認事項】
- 月額コスト: $30-50
- GCPプロジェクト作成が必要（10分）
- Cloud SQL設定が必要（10分）

代替案：SQLiteなら$0で即座に開発可能です。
どちらを選びますか？
1. Cloud SQL（月額$30-50）
2. SQLite（無料）」
```

### ケース3: 曖昧な要求
```markdown
User: "データベースを使ったアプリ"

AI判定: 曖昧 → デフォルトポリシー優先

AI応答:
「データベースアプリを開発します。
デフォルトでSQLite（無料）を使用します。
Cloud SQLなど外部DBが必要な場合はお知らせください。」
```

## 🔧 ワークフロー分岐

### Phase -2: ポリシー判定（新規追加）
```yaml
policy_decision_phase:
  duration: "10秒"

  step_1_analyze:
    - 要求テキストを解析
    - 外部サービスキーワード検出
    - コスト要件の確認

  step_2_decide:
    if: "外部サービス要求なし"
    then: "通常ワークフロー（Phase 0-5）"

    elif: "明示的な外部サービス要求"
    then: "外部API対応ワークフロー（Phase -1から）"

    else: "デフォルトポリシーで提案"

  step_3_inform:
    always: "選択したポリシーを明示"
    format: |
      📋 開発方針
      - 方式: {ローカル完結/外部サービス利用}
      - コスト: ${cost}
      - 人間の作業: {なし/30分}
```

## ✅ メリット

1. **後方互換性**: 従来の全自動開発は完全維持
2. **コスト最適**: デフォルトは常に$0
3. **柔軟性**: 明示的要求には対応
4. **透明性**: 選択理由を明確に説明
5. **選択権**: 代替案を常に提示

## 🚨 重要な原則

### やってはいけないこと
- ❌ 曖昧な要求で外部サービスを勝手に使う
- ❌ コストが発生する選択を勝手にする
- ❌ 人間の作業を勝手に増やす

### 必ずやること
- ✅ デフォルトは$0、全自動
- ✅ 外部サービスは明示的要求時のみ
- ✅ コストが発生する場合は必ず確認
- ✅ 代替案を提示

## 📱 モバイル対応ポリシー（NEW）

### 基本方針
```yaml
mobile_support:
  target_platforms:
    - "パソコン（デスクトップ）"
    - "iOS 18以降のスマートフォン"
  design: "レスポンシブデザイン必須"
  orientation: "縦向き・横向き両対応"
```

### レスポンシブ対応の標準
```yaml
responsive_requirements:
  breakpoints:
    mobile: "< 768px"
    tablet: "768px - 1024px"
    desktop: "> 1024px"

  quality_check:
    - "index.html/about.htmlのスマホ縦・横レイアウト確認"
    - "主要導線がタップ可能であること"
    - "簡易確認（ブラウザサイズ変更でOK）"
```

### ジャイロ操作（傾き操作）対応

**対象プロジェクト:**
```yaml
gyro_control_targets:
  condition_1:
    PROJECT_INFO.yaml:
      platform: "mobile"

  condition_2:
    PROJECT_INFO.yaml:
      mobile_features: ["tilt_control"]

  project_types:
    - "モバイルゲーム"
    - "傾き操作が必要なアプリ"
```

**実装標準:**
```yaml
gyro_implementation:
  reference_spec: "GYRO_CONTROLS_STANDARD.md v2.0 に完全準拠"

  key_requirements:
    ios_18_support:
      - "clickまたはtouchendイベント内でrequestPermission()を直接呼び出す"
      - "touchstartイベントは使用不可（iOS 18で動作しない）"
      - "GyroControlsクラスを経由しない"
      - "メニュー画面でもゲーム中でも許可取得可能"

    virtual_joystick_fallback:
      - "VirtualJoystick.js を必ず実装（必須）"
      - "画面右端に配置（canvas.width - 80, canvas.height - 100）"
      - "ジャイロ許可なしでもゲームプレイ可能"
      - "デフォルト操作モード: joystick"
      - "ジャイロ許可は**オプション**として提供"

    ui_requirements:
      - "操作モード切り替えボタン「🎯 傾き」「🕹️ スティック」"
      - "許可成功: ジャイロに切り替え、ジョイスティック非表示"
      - "許可拒否: ジョイスティックのままプレイ続行"
      - "ゲーム中でもモード切り替え可能"

    orientation_support:
      - "横向きモード: gamma（左右傾き）で上下移動、beta（前後傾き）で左右移動"
      - "縦向きモード: 通常のマッピング"
      - "isLandscape判定で自動切り替え"

    fallback:
      - "PC: キーボード操作"
      - "Android: 自動有効化（ジャイロ）"
      - "iOS拒否: バーチャルジョイスティック"

  implementation_location:
    agent: "Frontend Developer（8番）"
    method: "条件分岐で自動追加"
    no_dedicated_agent: true
```

**品質基準:**
```yaml
gyro_quality_standards:
  test_items:
    - "ジャイロ許可なしでもジョイスティックで遊べる（最重要）"
    - "ジャイロ許可成功時、ジョイスティックが非表示になる"
    - "ジャイロ許可拒否時、ジョイスティックのままプレイ可能"
    - "iPhone（iOS 18+）で許可ポップアップが表示される"
    - "Androidで自動的に有効化される"
    - "横向き・縦向き両方で正しく動作する"
    - "PCブラウザでエラーが発生しない"

  configuration:
    sensitivity: 3.5  # v2.0で高感度化
    deadZone: "2度"
    maxTilt: "20度"

  success_criteria:
    - "iOS 18完全対応"
    - "横向き/縦向き自動対応"
    - "95-98%成功率（ジャイロ操作必要時）"
```

**参考資料:**
- `GYRO_CONTROLS_STANDARD.md` - 完全な実装仕様
- `gradius-clone/src/controls/GyroControls.ts` - 成功事例

---

## 📝 実装チェックリスト

- [ ] Phase -2（ポリシー判定）を追加
- [ ] 要求解析ロジックを実装
- [ ] デフォルトポリシー優先を徹底
- [ ] 外部サービスは承認制
- [ ] 従来機能の完全維持
- [ ] モバイル対応ポリシー適用（レスポンシブ + ジャイロ操作）