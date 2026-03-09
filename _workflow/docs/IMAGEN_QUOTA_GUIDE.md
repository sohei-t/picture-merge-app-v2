# 📊 Google Imagen API クォータ管理ガイド

## 🎯 クォータの確認と増加方法

### 1. Web コンソールでの確認（推奨）

```bash
# ブラウザで開く
open "https://console.cloud.google.com/apis/api/aiplatform.googleapis.com/quotas?project=text-to-speech-app-1751525744"
```

または直接アクセス:
1. [Google Cloud Console](https://console.cloud.google.com) にアクセス
2. 「APIs & Services」→「Enabled APIs」
3. 「Vertex AI API」をクリック
4. 「Quotas & System Limits」タブ

### 2. 現在のクォータ制限

デフォルトのImagen API制限:
- **Online predictions per minute**: 5-10 リクエスト/分
- **Daily quota**: 制限なし（課金ベース）
- **Monthly spending limit**: $300無料クレジット内

### 3. クォータ増加申請

#### オプション A: セルフサービス（即時反映）

無料トライアル中でも、以下の制限は調整可能:
- 分間リクエスト数: 最大60まで増加可能
- 同時リクエスト数: 最大10まで

```bash
# CLIでの申請（利用可能な場合）
gcloud alpha services quota update \
  --service=aiplatform.googleapis.com \
  --consumer=projects/text-to-speech-app-1751525744 \
  --metric=aiplatform.googleapis.com/online_prediction_requests_per_base_model \
  --value=60
```

#### オプション B: サポートチケット

大規模な増加が必要な場合:
1. Cloud Console → Support
2. Create Case
3. Quota Increase Request
4. 理由: "Game development automation testing"

### 4. コスト管理設定

#### 予算アラートの設定

```bash
# 予算を作成（$5 = 約750円）
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="Imagen API Budget" \
  --budget-amount=5USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

#### 使用量の監視

```python
def check_usage():
    """今月の使用量を確認"""
    # Cloud Billing API を使用
    from google.cloud import billing

    client = billing.CloudBillingClient()
    # 実装...
```

## 💰 コスト計算

### 1ゲームあたりのコスト試算

| アセット | 枚数 | コスト |
|---------|------|--------|
| プレイヤー（4ポーズ） | 4 | $0.08 |
| 敵キャラ（3種×2ポーズ） | 6 | $0.12 |
| ボス（3ポーズ） | 3 | $0.06 |
| アイテム（5種） | 5 | $0.10 |
| 背景（3種） | 3 | $0.06 |
| エフェクト（5種） | 5 | $0.10 |
| **合計** | **26枚** | **$0.52** |

→ 1ゲーム約500円以内で収まります

## 🚀 推奨設定

### 開発環境用

```javascript
const QUOTA_CONFIG = {
  maxRequestsPerMinute: 30,     // 安全マージン付き
  maxImagesPerGame: 30,         // 1ゲーム上限
  maxCostPerGame: 1.00,         // $1上限
  retryDelay: 2000,              // 2秒待機
  maxRetries: 3
};
```

### プロダクション用

```javascript
const PROD_CONFIG = {
  maxRequestsPerMinute: 60,     // 最大値
  dailyLimit: 500,               // 1日上限
  monthlyBudget: 40.00,          // $40/月
  cacheEnabled: true,            // 再利用
  batchProcessing: true          // バッチ処理
};
```

## 📋 チェックリスト

### 初期設定
- [ ] Vertex AI API 有効化済み
- [ ] サービスアカウント作成済み
- [ ] 認証キー配置済み

### クォータ管理
- [ ] 現在のクォータ確認
- [ ] 必要に応じて増加申請
- [ ] 予算アラート設定

### コスト管理
- [ ] 1ゲームあたりの上限設定
- [ ] 月間予算の設定
- [ ] 使用量モニタリング

## ⚠️ 注意事項

1. **無料クレジット期間**
   - 90日間または$300まで
   - 期限後は自動課金

2. **レート制限**
   - 急激な増加は避ける
   - 段階的に増やす

3. **キャッシュ活用**
   - 同じキャラは再生成しない
   - 生成済みアセットをDBに保存