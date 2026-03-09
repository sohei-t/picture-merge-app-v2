# TECH_STACK.md - Picture Merge App v2 技術スタック決定書

## 1. 技術スタック概要

| レイヤー | 技術 | バージョン | 用途 |
|---------|------|-----------|------|
| **フロントエンド** | React | 18.x | UIフレームワーク |
| | TypeScript | 5.x (strict) | 型安全な開発 |
| | Vite | 5.x | ビルドツール・開発サーバー |
| | Tailwind CSS | 3.x | ユーティリティファーストCSS |
| | react-dropzone | 14.x | ドラッグ&ドロップファイル入力 |
| | Canvas API | (ブラウザネイティブ) | プレビュー表示・ドラッグ操作 |
| **バックエンド** | Python | 3.11+ | サーバーランタイム |
| | FastAPI | 0.115+ | REST APIフレームワーク |
| | uvicorn | 0.30+ | ASGIサーバー |
| | rembg | 2.0+ | 人物セグメンテーション (U2Net) |
| | Pillow | 10.x+ | 画像処理基盤 |
| | OpenCV (headless) | 4.9+ | 色調補正・影生成 |
| | python-multipart | 0.0.9+ | ファイルアップロード処理 |
| **テスト** | Vitest | 1.x | フロントエンドユニットテスト |
| | React Testing Library | 14.x | コンポーネントテスト |
| | pytest | 8.x | バックエンドテスト |
| | httpx | 0.27+ | FastAPI非同期テストクライアント |

---

## 2. フロントエンド技術選定

### 2.1 React 18 + TypeScript (strict)

**選定理由:**
- FINDY偏差値60+で高評価されるモダンフロントエンド構成
- React 18のConcurrent Renderingにより、重い画像処理中でもUIがスムーズに動作
- TypeScript strictモードで型安全性を保証し、バグの早期発見を実現
- AIがReactのベストプラクティスを最も多く学習しており、高品質コード生成に有利
- コンポーネント単位の構造がAIへの具体的指示と相性が良い

**バージョン:** React 18.3.x / TypeScript 5.5+

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| Vue 3 | Reactほどの型安全エコシステムがない。FINDY評価でもReact+TSが優位 |
| Svelte 5 | エコシステムがまだ成熟途上。テストツールチェーンが弱い |
| vanilla JS + Canvas | 状態管理が複雑化。UIコンポーネントの再利用性が低い |

### 2.2 Vite 5

**選定理由:**
- ESBuildベースの高速HMR（Hot Module Replacement）で開発体験が良好
- TypeScript・Tailwind CSSとのゼロコンフィグ統合
- ビルド時はRollupで最適化されたバンドル出力
- Create React Appは非推奨、Viteが現在のデファクトスタンダード

**バージョン:** Vite 5.4+

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| webpack | 設定が複雑。ビルド速度が遅い |
| Next.js | SSRが不要なローカルアプリに過剰。FastAPIバックエンドとの二重構成になる |
| Parcel | TypeScript strict + Tailwindの統合でViteに劣る |

### 2.3 Tailwind CSS 3

**選定理由:**
- ユーティリティファーストでスタイリングの一貫性と開発速度を両立
- JIT（Just-in-Time）モードで未使用CSSが自動除去され、バンドルサイズが最小化
- レスポンシブ・ダークモード対応が容易（本アプリはデスクトップ専用だが拡張性を確保）
- MUI等のUIライブラリよりも軽量で、カスタムデザインの自由度が高い

**バージョン:** Tailwind CSS 3.4+

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| MUI (Material UI) | バンドルサイズが大きい。本アプリのUIにはオーバースペック |
| CSS Modules | ユーティリティクラスの再利用性が低い |
| styled-components | ランタイムCSSのオーバーヘッド。型との統合がTailwindに劣る |

### 2.4 react-dropzone 14

**選定理由:**
- React向けファイルドロップの事実上の標準ライブラリ
- アクセシビリティ対応（キーボード操作、スクリーンリーダー）が組み込み
- ファイルタイプ・サイズのバリデーションが宣言的に記述可能
- 軽量（gzip ~7KB）で依存関係が少ない

**バージョン:** 14.x

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| react-dnd | 汎用D&Dライブラリでファイルドロップ特化ではない。設定が複雑 |
| ネイティブHTML D&D API | ブラウザ差異の吸収コードが必要。バリデーション手動実装 |
| FilePond | 高機能だがバンドルサイズが大きい。本アプリの要件にはオーバースペック |

### 2.5 Canvas API（ブラウザネイティブ）

**選定理由:**
- プレビュー画像の描画とドラッグ操作の両方をCanvas上で実現
- 追加ライブラリ不要でバンドルサイズに影響なし
- React RefとuseEffectで制御可能
- バックエンドから受け取った合成画像をそのまま描画するシンプルな構成

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| Konva.js / react-konva | 高機能だが、本アプリでは画像1枚描画+ドラッグのみなので過剰 |
| Fabric.js | テキスト・図形操作向け。写真合成プレビューには不向き |
| img要素 + CSS transform | ドラッグ操作のヒットテストが困難。Canvas APIの方が制御しやすい |

---

## 3. バックエンド技術選定

### 3.1 Python 3.11+

**選定理由:**
- rembg、Pillow、OpenCVなど画像処理ライブラリの最も豊富なエコシステム
- 3.11以降のパフォーマンス改善（CPython高速化 10-25%）
- async/awaitネイティブサポートでFastAPIとの相性が良い
- Mac mini M4でネイティブ動作

**バージョン:** 3.11+（3.12推奨）

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| Node.js | 画像処理ライブラリ（sharp等）はPythonほど充実していない。rembg相当がない |
| Rust | 開発速度が遅い。画像処理エコシステムがPythonに劣る |
| Go | 画像処理ライブラリが少ない。rembg相当のセグメンテーション実装が困難 |

### 3.2 FastAPI 0.115+

**選定理由:**
- Pydanticベースの自動バリデーション・ドキュメント生成（Swagger UI）
- async対応で画像処理の並列実行が可能
- 型ヒント活用による開発者体験の良さ
- `/docs` エンドポイントで自動生成されるAPI仕様書がFINDY評価に寄与
- REST APIのみの構成でシンプル（WebSocket不要の設計判断）

**バージョン:** 0.115+

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| Flask | async非対応。バリデーション・ドキュメント生成が手動 |
| Django REST Framework | ORMベースの重厚な構成。本アプリにはオーバースペック |
| Starlette | FastAPIの基盤だが、Pydantic統合やSwagger UIの自動生成がない |

### 3.3 rembg 2.0+ (U2Net)

**選定理由:**
- `pip install rembg` のみで動作する手軽さ
- U2Netモデルによる高精度な人物セグメンテーション
- アルファマット出力で髪の毛のエッジも自然に処理
- Mac mini M4でCPU推論 1-3秒/枚の実用的な速度
- 初回起動時にモデルを自動ダウンロード・キャッシュ

**バージョン:** 2.0+

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| Apple Vision Framework (pyobjc) | macOS限定。pyobjcの依存関係が複雑。ポートフォリオ公開時の再現性が低い |
| MediaPipe | セグメンテーション精度がU2Netに劣る（特に髪の毛のエッジ） |
| SAM (Segment Anything) | モデルサイズが大きく（>2GB）、推論速度が遅い。本アプリには過剰 |
| backgroundremover | rembgのフォークで更新頻度が低い |

### 3.4 Pillow 10.x+

**選定理由:**
- Python画像処理の事実上の標準ライブラリ
- RGBA画像のアルファブレンディング、リサイズ、フォーマット変換をカバー
- base64エンコード/デコードとの統合が容易
- HEIC対応は pillow-heif プラグインで拡張可能（P1機能）

**バージョン:** 10.4+

### 3.5 OpenCV (opencv-python-headless) 4.9+

**選定理由:**
- `headless` パッケージでGUI依存を排除し、サーバー環境で安定動作
- LAB色空間でのヒストグラムマッチング（色調補正）が標準機能
- ガウシアンブラー・楕円描画による高品質な影生成
- NumPy配列との相互運用でPillowとシームレスに連携

**バージョン:** 4.9+

**代替案と却下理由:**
| 代替案 | 却下理由 |
|--------|---------|
| scikit-image | OpenCVほど高速でない。色調補正の実装が複雑 |
| Pillowのみ | 色調補正（LABヒストグラムマッチング）の実装が困難。影生成の品質が低い |
| ImageMagick (Wand) | Pythonバインディングの品質がOpenCVに劣る。インストールが複雑 |

### 3.6 python-multipart 0.0.9+

**選定理由:**
- FastAPIの`UploadFile`が内部的に依存
- multipart/form-dataのパースに必須
- 軽量で追加の設定不要

### 3.7 uvicorn 0.30+

**選定理由:**
- FastAPI公式推奨のASGIサーバー
- 開発時のホットリロード対応（`--reload`）
- 本番モードでのワーカープロセス管理

---

## 4. テスト技術選定

### 4.1 Vitest 1.x + React Testing Library 14.x

**選定理由:**
- Viteプロジェクトとのゼロコンフィグ統合（vite.config.ts共有）
- Jestと互換のAPI（`describe`, `it`, `expect`）で学習コスト最小
- React Testing Libraryでユーザー視点のコンポーネントテストが記述可能
- HMR対応のウォッチモードで開発中のテスト実行が高速

**カバレッジ目標:**
- コンポーネント: 80%+
- カスタムフック: 90%+
- ユーティリティ関数: 95%+

### 4.2 pytest 8.x + httpx 0.27+

**選定理由:**
- Pythonテストの事実上の標準
- httpxのAsyncClientでFastAPIのTestClientとして使用（公式推奨パターン）
- fixtureベースのテストデータ管理
- pytest-covでカバレッジ計測

**カバレッジ目標:**
- APIエンドポイント: 90%+
- 画像処理パイプライン: 85%+
- エラーハンドリング: 90%+

---

## 5. 開発ツール・インフラ

| ツール | バージョン | 用途 |
|--------|-----------|------|
| Node.js | 18+ (LTS) | フロントエンドランタイム |
| npm | 10+ | パッケージ管理（フロントエンド） |
| pip | 23+ | パッケージ管理（バックエンド） |
| venv | (標準ライブラリ) | Python仮想環境 |
| ESLint | 8.x | コード品質チェック |
| Prettier | 3.x | コードフォーマット |

---

## 6. HEIC対応（P1）

| パッケージ | 用途 | 備考 |
|-----------|------|------|
| pillow-heif | HEIC/HEIFデコード | Pillowプラグイン。`pip install pillow-heif` で追加 |

**判断:** P1機能としてオプション。JPEG/PNG/WebPの3形式はP0で必須対応。
HEIC入力時に pillow-heif が未インストールの場合は、ユーザーフレンドリーなエラーメッセージで変換を案内。

---

## 7. 外部API・クラウドサービス

**不使用**（$0運用）

- 全処理をローカルで完結
- 外部通信なし（rembgモデルの初回ダウンロードのみ例外）
- クラウドデプロイ不要（ローカルサーバー構成）

---

## 8. アーキテクチャ方針

| 方針 | 詳細 |
|------|------|
| フロントエンド/バックエンド分離 | React (Vite) + FastAPI の2プロセス構成 |
| REST APIのみ | WebSocket不使用。プレビューはPOST /api/merge (preview_mode=true) で実現 |
| サーバーサイドキャッシュ | セグメンテーション結果をLRU方式でインメモリ保持（ID参照でmerge時のbase64再送回避） |
| 画像処理はバックエンド集約 | Pillow + OpenCVのフルパワーを活用。フロントはUI操作に専念 |
| プレビュー最適化 | preview_mode=true: 512x512 JPEG (quality=70) で高速返却 |
| フルレンダリング | preview_mode=false: 指定サイズ PNG で高品質出力 |

---

## 9. パッケージ一覧

### 9.1 フロントエンド (package.json)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-dropzone": "^14.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@testing-library/react": "^14.2.0",
    "@testing-library/jest-dom": "^6.4.0",
    "@testing-library/user-event": "^14.5.0",
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.57.0",
    "postcss": "^8.4.0",
    "prettier": "^3.3.0",
    "tailwindcss": "^3.4.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0",
    "vitest": "^1.6.0",
    "jsdom": "^24.0.0"
  }
}
```

### 9.2 バックエンド (requirements.txt)

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
rembg>=2.0.0
Pillow>=10.4.0
opencv-python-headless>=4.9.0
python-multipart>=0.0.9
pydantic>=2.7.0

# P1: HEIC対応（オプション）
# pillow-heif>=0.16.0

# テスト
pytest>=8.2.0
httpx>=0.27.0
pytest-asyncio>=0.23.0
pytest-cov>=5.0.0
```
