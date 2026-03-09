# 🎨 Frontend-Design スキル使用ガイド

## 📋 概要

Anthropic公式の `frontend-design` スキルは、汎用的なAIデザインを避け、独自性のある高品質なフロントエンドインターフェースを生成する強力なツールです。

## 🚀 重要：必ず使用すべき場面

### 1. **HTMLドキュメント生成時**
- about.html
- index.html
- ランディングページ
- ショーケースページ

### 2. **UI/UXデザイン時**
- コンポーネント設計
- ページレイアウト
- インタラクティブ要素
- ダッシュボード

### 3. **プロトタイプ作成時**
- MVPのUI
- デザインバリエーション
- A/Bテスト用デザイン

## 📝 効果的な使い方

### 基本的な呼び出し方

```markdown
"use the frontend design skill"を明示的に宣言してから、具体的な要求を記述
```

### 推奨プロンプトパターン

#### パターン1: 詳細指定型
```
"use the frontend design skill.
Create a [具体的なコンポーネント/ページ] for [プロジェクト名].
Include as many relevant features and interactions as possible.
Add thoughtful details like hover states, transitions, and micro-interactions.
Go beyond the basics to create a fully-featured implementation.
Don't hold back - make it exceptional."
```

#### パターン2: デザイン方向性指定型
```
"use the frontend design skill.
Create a [minimalist/maximalist/retro-futuristic/brutalist] design for [要素].
Focus on [specific aspects: typography/color/layout/animation].
Make it distinctive and memorable."
```

#### パターン3: バリエーション生成型
```
"use the frontend design skill.
Generate 5 different design variants for [コンポーネント].
Each should have a distinct aesthetic approach.
Vary the color schemes, typography, and interaction patterns."
```

## ⚠️ 避けるべきパターン（AIっぽさを防ぐ）

### ❌ 避けるべきフォント
- Inter
- Roboto
- Arial
- システムフォント

### ❌ 避けるべきカラースキーム
- 紫のグラデーション（特に白背景）
- 予測可能な青系配色
- 一般的なマテリアルデザインカラー

### ❌ 避けるべきレイアウト
- 中央寄せカード
- 標準的なサイドバーレイアウト
- 汎用的なヒーローセクション

## ✅ 推奨される要素

### 🎯 デザイン哲学
- **意図的な選択**: すべてのデザイン決定に理由を持つ
- **一貫性**: 選んだ方向性を徹底的に追求
- **独自性**: 他にはないユニークな要素を含む

### 🎨 推奨要素
- カスタムフォントの組み合わせ
- 独特なカラーパレット
- インタラクティブな要素
- マイクロインタラクション
- トランジション効果
- パララックス効果（適切な場合）
- SVGアニメーション
- カスタムカーソル（適切な場合）

## 📋 実装例

### 例1: about.html 生成
```javascript
// エージェントへの指示
const prompt = `
use the frontend design skill.
Create an about/showcase page for our ToDo App project.
Include:
- Hero section with animated title
- Interactive feature showcase
- Tech stack visualization with hover effects
- Development timeline with scroll animations
- Team section with creative layouts
- Contact form with validation animations
Make it visually stunning and professional.
Use a modern, clean aesthetic with subtle animations.
`;
```

### 例2: ダッシュボード生成
```javascript
const prompt = `
use the frontend design skill.
Create an analytics dashboard with:
- Real-time data visualization
- Interactive charts and graphs
- Customizable widget layout
- Dark/light theme toggle
- Responsive grid system
Include as many relevant features as possible.
Make it feel premium and data-rich.
`;
```

### 例3: ランディングページ生成
```javascript
const prompt = `
use the frontend design skill.
Create a landing page for an AI security startup.
Style: Bold, trustworthy, cutting-edge
Include:
- Animated hero with particle effects
- Feature cards with 3D transforms
- Testimonial carousel with smooth transitions
- Pricing table with hover states
- Newsletter signup with micro-interactions
Go beyond basics - make it memorable.
`;
```

## 🔄 ワークフローへの組み込み

### Phase 2: 実装フェーズ
```yaml
frontend_implementation:
  step_1: "use the frontend design skill を宣言"
  step_2: "詳細な要件を指定"
  step_3: "生成されたコードをレビュー"
  step_4: "必要に応じてバリエーションを要求"
  step_5: "テストとの整合性確認"
```

### Phase 5: 完成処理フェーズ
```yaml
about_html_generation:
  must_use: "frontend-design skill"
  requirements:
    - "プロジェクトのショーケース"
    - "インタラクティブな要素"
    - "プロフェッショナルな仕上がり"
    - "ユニークで記憶に残るデザイン"
```

## 💡 Tips & Tricks

### 1. **具体性が鍵**
曖昧な指示（"make it pretty"）ではなく、具体的な要望を伝える

### 2. **コンテキストを提供**
プロジェクトの性質、ターゲットユーザー、ブランドイメージを伝える

### 3. **繰り返しを活用**
初回生成が期待と異なる場合、より具体的な指示で再生成

### 4. **バリエーションを活用**
5つのバリアントを生成して、最適なものを選択

### 5. **既存デザインとの統合**
プロジェクトの既存UIと調和するよう指示

## 📊 品質チェックリスト

- [ ] frontend-design スキルを明示的に呼び出したか
- [ ] 具体的で詳細な要件を指定したか
- [ ] 汎用的なAIデザインを避けているか
- [ ] インタラクティブな要素が含まれているか
- [ ] レスポンシブデザインか
- [ ] アクセシビリティが考慮されているか
- [ ] パフォーマンスが最適化されているか
- [ ] ユニークで記憶に残るデザインか

## 🚨 トラブルシューティング

### 問題: スキルが動作しない
**解決策**: "use the frontend design skill" を必ず最初に宣言

### 問題: 汎用的なデザインになる
**解決策**: より具体的な指示、デザイン方向性の明確化

### 問題: 期待と異なるスタイル
**解決策**: 5つのバリアント生成、参考デザインの提示

## 📚 参考資料

- [Anthropic公式ドキュメント](https://docs.anthropic.com)
- [Claude Code Skills](https://github.com/anthropics/claude-code)
- [Frontend Design Best Practices](https://www.anthropic.com/blog)