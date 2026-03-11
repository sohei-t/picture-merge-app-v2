# Picture Merge App v2

AI対応 高品質写真合成Webアプリケーション

## 概要

2枚の人物写真から人物をAIで高精度に切り抜き、同じ場所に一緒にいるかのように自然に合成するWebアプリケーションです。動画生成AI（Kling, Runway, Pika等）に渡す元画像として、「2人が一緒に写っている1枚の写真」として認識される品質を実現します。

## 主な機能

- **写真入力（2枚）**: ドラッグ&ドロップまたはファイル選択で人物写真を入力（JPEG/PNG/WebP対応、最大20MB/枚）。個別クリア対応
- **AI人物セグメンテーション**: rembg（BiRefNet優先、U2Netフォールバック）による高精度な自動背景除去。低コントラスト境界でも高い精度
- **色調補正**: LAB色空間のA/Bチャネルのみをマッチングし、明るさを変えずに色温度を自動統一
- **影生成**: ガウシアンブラー楕円による自然な足元影を自動生成
- **リアルタイムプレビュー**: パラメータ変更が即座にプレビューに反映。Canvas上で人物を上下左右にドラッグして位置調整
- **レイヤー順序切替**: どちらの人物を前面に表示するかワンクリックで切替
- **トリミング機能**: 合成画像の任意範囲を選択して切り出しダウンロード（上半身だけ等）
- **高品質出力**: フル解像度PNG出力。正方形（1024x1024）、横長（1280x720）、縦長（720x1280）等のプリセット対応

## 技術スタック

### フロントエンド
- React 18 + TypeScript（strict mode）
- Vite 5（ビルドツール）
- Tailwind CSS 3（スタイリング）
- react-dropzone（ファイル入力）
- Canvas API（プレビュー・ドラッグ操作）

### バックエンド
- Python 3.11+ / FastAPI（REST APIサーバー）
- rembg 2.0+（BiRefNet/U2Net人物セグメンテーション）
- Pillow 10.x+（画像処理基盤）
- OpenCV 4.9+（色調補正・影生成）
- uvicorn（ASGIサーバー）

### テスト
- Vitest + React Testing Library（フロントエンド）
- pytest + httpx（バックエンド）

## 起動方法

`launch_app.command` をダブルクリックすると、バックエンドサーバーとフロントエンド開発サーバーが自動的に起動し、ブラウザが開きます。

### 手動起動

```bash
# バックエンド起動
cd backend/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000

# フロントエンド起動（別ターミナル）
cd frontend/
npm install
npm run dev
```

ブラウザで http://localhost:5173 を開いてください。

## 使い方

1. 2枚の人物写真をドラッグ&ドロップ
2. 自動でセグメンテーション・合成プレビューが表示
3. プレビュー上で人物をドラッグして位置を調整（上下左右対応）
4. 設定パネルでスケール・背景色・レイヤー順序等を調整
5. 「ダウンロード」ボタンでフル解像度PNG取得
6. 「トリミング」ボタンで任意の範囲を切り出してダウンロード

## 動作環境

- macOS（Mac mini M4推奨）
- Chrome / Edge（最新版）
- Python 3.11+
- Node.js 18+

## ライセンス

MIT

---

Generated with [Claude Code](https://github.com/anthropics/claude-code)
