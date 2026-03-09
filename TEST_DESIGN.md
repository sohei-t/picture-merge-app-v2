# TEST_DESIGN.md - Picture Merge App v2 テスト設計書

## 1. テスト戦略概要

| 項目 | 値 |
|------|-----|
| バックエンドフレームワーク | pytest + httpx (AsyncClient) |
| フロントエンドフレームワーク | Vitest + React Testing Library |
| E2Eテスト | Playwright MCP (テストシナリオ定義) |
| カバレッジ目標 (バックエンド) | 85%+ |
| カバレッジ目標 (フロントエンド) | 80%+ |
| クリティカルパスカバレッジ | 100% |

### カバレッジ目標の内訳

| カテゴリ | 目標 | 対象 |
|---------|------|------|
| セグメンテーションパイプライン | 100% | rembg呼び出し、BBox算出、足元検出、アルファマット後処理 |
| 合成パイプライン | 100% | 色調補正、スケール計算、影生成、最終合成、出力 |
| APIエンドポイント | 100% | /api/segment, /api/merge, /api/health |
| バリデーション | 100% | ファイル形式、サイズ、パラメータ制約 |
| フロントエンド状態管理 | 90%+ | AppPhase遷移、エラーハンドリング |
| UIコンポーネント | 80%+ | ドロップゾーン、設定パネル、Canvas |
| ユーティリティ | 90%+ | fileValidation, imageUtils, downloadUtils |

---

## 2. バックエンドテスト (pytest + httpx)

### 2.1 POST /api/segment テスト

#### 正常系

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-SEG-001 | JPEG画像のセグメンテーション | 200 OK。id (seg_で始まる)、segmented_image (data:image/png;base64,...)、bbox (x,y,width,height > 0)、foot_y (> 0)、original_size、processing_time_ms が返却される | P0 |
| BE-SEG-002 | PNG画像のセグメンテーション | 200 OK。JPEG同様のレスポンス構造。透過PNG入力も正常処理される | P0 |
| BE-SEG-003 | WebP画像のセグメンテーション | 200 OK。JPEG同様のレスポンス構造 | P0 |
| BE-SEG-004 | segmentation_idの一意性 | 2回呼び出して異なるIDが返却される。ID形式が `seg_[a-f0-9]{8}` に一致する | P0 |
| BE-SEG-005 | BBoxの正当性検証 | bbox.x >= 0, bbox.y >= 0, bbox.width > 0, bbox.height > 0。bbox.x + bbox.width <= original_size.width | P0 |
| BE-SEG-006 | foot_yの正当性検証 | foot_y == bbox.y + bbox.height。foot_y <= original_size.height | P0 |
| BE-SEG-007 | processing_time_msの存在 | processing_time_ms >= 0 の整数値が返却される | P1 |
| BE-SEG-008 | 長辺4000px超画像の自動リサイズ | 5000x3000pxの入力画像が正常に処理される。レスポンスのoriginal_sizeは元のサイズを保持する | P1 |
| BE-SEG-009 | EXIF回転の自動補正 | EXIF Orientation=6(90度回転)の画像が正しい向きで処理される | P1 |
| BE-SEG-010 | セグメンテーション結果のキャッシュ保存 | segment成功後、同じIDで /api/merge から参照可能 | P0 |

#### 異常系

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-SEG-011 | 非画像ファイル (PDF) の送信 | 400 Bad Request。error="invalid_image"、message に「対応していない画像形式」を含む | P0 |
| BE-SEG-012 | 非画像ファイル (テキスト) の送信 | 400 Bad Request。error="invalid_image" | P0 |
| BE-SEG-013 | Content-Type偽装 (image/jpegを名乗るPDF) | 400 Bad Request。マジックバイト検証で拒否される | P0 |
| BE-SEG-014 | 20MBを超えるファイル | 413 Payload Too Large。error="file_too_large" | P0 |
| BE-SEG-015 | 空ファイル (0バイト) | 400 Bad Request | P1 |
| BE-SEG-016 | 人物が写っていない風景画像 | 422 Unprocessable Entity。error="segmentation_failed"。message に「人物を検出できませんでした」を含む | P0 |
| BE-SEG-017 | ファイルフィールド未指定 | 422 Validation Error | P1 |
| BE-SEG-018 | 破損した画像ファイル | 400 Bad Request または 500 Internal Server Error（エラーメッセージ付き） | P1 |

### 2.2 POST /api/merge テスト

#### 正常系

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-MRG-001 | preview_mode=true でプレビュー合成 | 200 OK。merged_image が `data:image/jpeg;base64,` で始まる。output_size.width == 512, output_size.height == 512 | P0 |
| BE-MRG-002 | preview_mode=false でフル解像度合成 | 200 OK。merged_image が `data:image/png;base64,` で始まる。output_size が settings 指定値と一致 | P0 |
| BE-MRG-003 | デフォルト設定での合成 | settings未指定で200 OK。出力サイズ 1024x1024、白背景 | P0 |
| BE-MRG-004 | background_color パラメータ反映 | background_color="#FF0000" を指定し、出力画像の背景ピクセルが赤であることを検証 | P1 |
| BE-MRG-005 | output_width / output_height 指定 | output_width=1280, output_height=720 指定で、出力サイズが一致する | P1 |
| BE-MRG-006 | person1.x / person2.x 位置指定 | person1.x=0.2, person2.x=0.8 で、人物が指定位置に配置される | P1 |
| BE-MRG-007 | person.scale 指定 | person1.scale=1.5 で人物がスケーリングされる | P1 |
| BE-MRG-008 | person.y_offset 指定 | person1.y_offset=50 で人物がY方向にオフセットされる | P1 |
| BE-MRG-009 | shadow.enabled=true で影あり | shadow.enabled=true で合成。出力画像の足元付近に暗いピクセルが存在する | P1 |
| BE-MRG-010 | shadow.enabled=false で影なし | shadow.enabled=false で合成。足元付近が背景色のままである | P1 |
| BE-MRG-011 | shadow.intensity 変更 | intensity=0.1 と intensity=1.0 で影の濃さが異なる | P1 |
| BE-MRG-012 | color_correction=true で色調補正あり | 色調補正有効で合成処理がエラーなく完了する | P0 |
| BE-MRG-013 | color_correction=false で色調補正なし | 色調補正無効でも合成処理が正常完了する | P0 |
| BE-MRG-014 | processing_time_ms の返却 | processing_time_ms >= 0 の整数値が含まれる | P1 |
| BE-MRG-015 | preview_mode=true のレスポンスサイズ | JPEG base64 のサイズが PNG base64 より小さい | P1 |

#### 異常系

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-MRG-016 | 存在しない image1_id | 404 Not Found。error="invalid_segment_id" | P0 |
| BE-MRG-017 | 存在しない image2_id | 404 Not Found。error="invalid_segment_id" | P0 |
| BE-MRG-018 | image1_id と image2_id 両方無効 | 404 Not Found | P0 |
| BE-MRG-019 | person1.scale が範囲外 (0.1) | 400 Bad Request。validation_error | P0 |
| BE-MRG-020 | person1.scale が範囲外 (3.0) | 400 Bad Request。validation_error | P0 |
| BE-MRG-021 | person1.x が範囲外 (-0.1) | 400 Bad Request。validation_error | P0 |
| BE-MRG-022 | person1.x が範囲外 (1.5) | 400 Bad Request。validation_error | P0 |
| BE-MRG-023 | shadow.intensity が範囲外 (2.0) | 400 Bad Request。validation_error | P1 |
| BE-MRG-024 | output_width が範囲外 (10) | 400 Bad Request。validation_error (ge=64) | P1 |
| BE-MRG-025 | output_width が範囲外 (5000) | 400 Bad Request。validation_error (le=4096) | P1 |
| BE-MRG-026 | background_color が不正形式 ("red") | 400 Bad Request。validation_error (hex pattern) | P1 |
| BE-MRG-027 | リクエストボディなし | 422 Validation Error | P1 |
| BE-MRG-028 | image1_id 未指定 | 422 Validation Error | P0 |

### 2.3 画像処理パイプライン ユニットテスト

#### 色調補正 (color_correction.py)

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-CLR-001 | 同一画像同士の色調補正 | 入力画像と同一（または極めて近い）出力。LABチャンネルの差分が閾値以内 | P0 |
| BE-CLR-002 | 暗い画像 → 明るい画像基準で補正 | 出力画像のLチャンネル平均値が参照画像に近づく | P0 |
| BE-CLR-003 | 暖色画像 → 寒色画像基準で補正 | 出力画像のA/Bチャンネル平均値が参照画像に近づく | P1 |
| BE-CLR-004 | アルファチャンネル保持 | RGBA入力でアルファチャンネルが変更されない | P0 |
| BE-CLR-005 | ピクセル値の0-255クランプ | 出力画像の全ピクセルが0-255の範囲内 | P0 |
| BE-CLR-006 | 1x1ピクセル画像の補正 | エラーなく処理される（std=0のエッジケース処理） | P1 |

#### 影生成 (shadow_generator.py)

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-SHD-001 | 影の生成位置 | 影の中心が指定した foot_x, foot_y に位置する | P0 |
| BE-SHD-002 | 影のサイズ | 影の幅が person_width * 0.8 に近似、高さが person_width * 0.15 に近似 | P0 |
| BE-SHD-003 | 影の不透明度 | intensity=1.0 で最大不透明度が 255 * 0.6 = 153 に近似 | P0 |
| BE-SHD-004 | intensity=0.0 で影なし | 影レイヤーの全ピクセルのアルファ値が 0 | P1 |
| BE-SHD-005 | ガウシアンブラー適用 | 影の境界がグラデーション状（隣接ピクセルとの差分が小さい） | P1 |
| BE-SHD-006 | キャンバスサイズとの一致 | 出力影レイヤーのサイズがキャンバスサイズと一致する | P0 |

#### 自動スケール計算 (auto_scale.py)

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-SCL-001 | 同じ身長の2人 | height_ratio ≈ 1.0。scale差が小さい | P0 |
| BE-SCL-002 | 身長差が大きい (2倍) | height_ratio がクランプされ 0.8-1.2 範囲内 | P0 |
| BE-SCL-003 | 身長差が小さい (1.1倍) | height_ratio がそのまま使用される (was_clamped=false) | P0 |
| BE-SCL-004 | クランプ上限 (ratio=1.5) | was_clamped=true。clamped_ratio=1.2 | P0 |
| BE-SCL-005 | クランプ下限 (ratio=0.5) | was_clamped=true。clamped_ratio=0.8 | P0 |
| BE-SCL-006 | 手動スケール値の優先 | settings.personN.scale が設定されている場合、自動スケールより優先される | P0 |
| BE-SCL-007 | キャンバスに対する相対スケール | 人物がキャンバスの70%程度の高さになる | P1 |

#### アルファマット精密化

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-ALF-001 | ガウシアンブラー適用後のエッジ平滑化 | アルファマスクのエッジ部分の遷移が滑らか（急激な0→255変化がない） | P0 |
| BE-ALF-002 | アルファマスクの形状保持 | ブラー適用後も人物の大まかな形状が維持される | P0 |
| BE-ALF-003 | 完全透明画像の検出 | 全ピクセルが alpha=0 の場合に人物未検出として判定される | P0 |

### 2.4 SegmentationStore (LRUキャッシュ) テスト

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-STO-001 | put/get の基本動作 | put したエントリが get で取得できる | P0 |
| BE-STO-002 | 存在しないIDのget | None が返却される | P0 |
| BE-STO-003 | MAX_ENTRIES (10件) 超過 | 11件目を追加すると最も古いエントリが削除される | P0 |
| BE-STO-004 | LRU順序の更新 | get 呼び出しでアクセス順序が更新される。頻繁にアクセスされたものは削除されない | P0 |
| BE-STO-005 | clear の動作 | clear 後に全エントリが取得不可になる | P1 |
| BE-STO-006 | 同一IDへの再put | 既存エントリが上書きされ、LRU順序が末尾に移動する | P1 |

### 2.5 GET /api/health テスト

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-HLT-001 | 正常時のレスポンス | 200 OK。status="ok"、rembg_loaded=true/false、version="2.0.0" | P0 |
| BE-HLT-002 | レスポンス構造の検証 | status, rembg_loaded, version の全フィールドが存在する | P0 |
| BE-HLT-003 | rembg未ロード時 | rembg_loaded=false が返却される | P1 |

### 2.6 ミドルウェア・バリデーションテスト

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| BE-MID-001 | CORS ヘッダー確認 | localhost:5173 からのリクエストに適切なCORSヘッダーが付与される | P0 |
| BE-MID-002 | 許可されないオリジン | localhost:3000 からのリクエストがCORSで拒否される | P1 |
| BE-MID-003 | マジックバイト検証 (JPEG: FF D8) | JPEG画像がマジックバイト検証を通過する | P0 |
| BE-MID-004 | マジックバイト検証 (PNG: 89 50 4E 47) | PNG画像がマジックバイト検証を通過する | P0 |
| BE-MID-005 | マジックバイト検証 (WebP: 52 49 46 46) | WebP画像がマジックバイト検証を通過する | P0 |

---

## 3. フロントエンドテスト (Vitest + React Testing Library)

### 3.1 コンポーネント単体テスト

#### ImageDropzone / DropZone

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-DRZ-001 | ドロップゾーンの初期表示 | 2つのドロップゾーンが表示される。「写真をドロップ」的なテキストが表示される | P0 |
| FE-DRZ-002 | JPEG画像のドロップ | onDrop コールバックが呼ばれる。サムネイルが表示される | P0 |
| FE-DRZ-003 | PNG画像のドロップ | onDrop コールバックが呼ばれる | P0 |
| FE-DRZ-004 | WebP画像のドロップ | onDrop コールバックが呼ばれる | P0 |
| FE-DRZ-005 | 非画像ファイルのドロップ | エラーメッセージ「対応していないファイル形式です」が表示される。onDrop は呼ばれない | P0 |
| FE-DRZ-006 | 20MB超ファイルのドロップ | エラーメッセージ「ファイルサイズが20MBを超えています」が表示される | P0 |
| FE-DRZ-007 | ファイル選択ダイアログからの入力 | クリックでダイアログが開く。選択後にonDropが呼ばれる | P1 |
| FE-DRZ-008 | ドロップゾーンのドラッグオーバースタイル | ファイルをドラッグ中にハイライトスタイルが適用される | P1 |
| FE-DRZ-009 | 画像入力後のサムネイル表示 | 入力後、ドロップゾーンがサムネイル表示に切り替わる | P0 |

#### SettingsPanel

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-SET-001 | 初期表示でデフォルト値 | 背景色=#FFFFFF、サイズ=1024x1024、scale=1.0、影=ON (0.5)、色調補正=ON | P0 |
| FE-SET-002 | 背景色カラーピッカー変更 | onChange が新しい色値で呼ばれる | P0 |
| FE-SET-003 | 出力サイズプリセット選択 | "横長 16:9" 選択で width=1280, height=720 に更新される | P0 |
| FE-SET-004 | スケールスライダー操作 | スライダーを動かすと 0.5-2.0 の範囲で onChange が呼ばれる | P0 |
| FE-SET-005 | 影ON/OFFトグル | トグルで shadow.enabled が切り替わる | P0 |
| FE-SET-006 | 影強度スライダー | 0.0-1.0 の範囲で intensity が更新される | P1 |
| FE-SET-007 | 色調補正ON/OFFトグル | colorCorrection が切り替わる | P0 |
| FE-SET-008 | カスタムサイズ入力 | 幅・高さに数値入力可能。64-4096 の範囲バリデーション | P1 |
| FE-SET-009 | パネル折りたたみ | 折りたたみボタンで設定パネルが開閉する | P1 |
| FE-SET-010 | 設定変更時のデバウンス | スライダー操作後 300ms 以内は再度呼び出されない | P1 |

#### PreviewCanvas / MergeCanvas

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-CVS-001 | プレビュー画像の描画 | base64画像がCanvas上に描画される | P0 |
| FE-CVS-002 | Canvas のレスポンシブサイズ | 親コンテナ幅に合わせて可変する。max-width: 640px | P1 |
| FE-CVS-003 | プレビュー未取得時の表示 | プレースホルダーまたは空のCanvas が表示される | P1 |
| FE-CVS-004 | 読み込み中の表示 | ローディングスピナーが表示される | P1 |

#### DownloadButton / ActionBar

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-DLB-001 | PREVIEW状態でダウンロードボタン有効 | ボタンがクリック可能である | P0 |
| FE-DLB-002 | IDLE状態でダウンロードボタン無効 | ボタンが disabled である | P0 |
| FE-DLB-003 | ダウンロードクリックでコールバック呼び出し | onDownload が呼ばれる | P0 |
| FE-DLB-004 | MERGING状態でローディング表示 | ボタンにスピナーが表示される | P1 |
| FE-DLB-005 | リセットボタンクリック | onReset が呼ばれる | P0 |
| FE-DLB-006 | COMPLETE状態で「もう1枚作る」ボタン | リセット機能を持つボタンが表示される | P1 |

#### StatusIndicator

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-STS-001 | IDLE状態の表示 | 初期状態のUIが表示される | P0 |
| FE-STS-002 | SEGMENTING状態でスピナー表示 | スピナーと「切り抜いています...」テキストが表示される | P0 |
| FE-STS-003 | ERROR状態でエラーメッセージ表示 | エラーメッセージとリトライ/リセットボタンが表示される | P0 |
| FE-STS-004 | COMPLETE状態で成功メッセージ | 成功メッセージが表示される | P1 |

#### ErrorBoundary

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-ERR-001 | 子コンポーネントのエラーをキャッチ | エラーが発生した子コンポーネントの代わりにフォールバックUIが表示される | P0 |
| FE-ERR-002 | 正常時は子コンポーネントを表示 | エラーがない場合、子コンポーネントがそのまま表示される | P0 |

### 3.2 カスタムフックテスト

#### useSegmentation

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-HSG-001 | segment() 呼び出しでAPI実行 | POST /api/segment が呼ばれる。成功時に person1/person2 に結果がセットされる | P0 |
| FE-HSG-002 | 処理中の isProcessing 状態 | API呼び出し中は isProcessing=true。完了後 false | P0 |
| FE-HSG-003 | API失敗時のエラーハンドリング | 400/422エラー時にエラー状態がセットされる | P0 |
| FE-HSG-004 | 2枚同時セグメンテーション | 2枚を同時に送信し、両方の結果がセットされる | P0 |
| FE-HSG-005 | ネットワークエラー時 | エラー状態がセットされ、リトライ可能な状態になる | P1 |

#### useMerge

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-HMG-001 | fetchPreview() でプレビュー取得 | POST /api/merge (preview_mode=true) が呼ばれる。previewImage がセットされる | P0 |
| FE-HMG-002 | fetchFullResolution() でフル画像取得 | POST /api/merge (preview_mode=false) が呼ばれる | P0 |
| FE-HMG-003 | 処理中の isLoading 状態 | API呼び出し中は isLoading=true | P0 |
| FE-HMG-004 | 404エラー時の自動再セグメンテーション | invalid_segment_id 受信時に再セグメンテーションフローが開始される | P1 |
| FE-HMG-005 | パラメータ変更時のデバウンス動作 | 設定変更後 300ms 経過してからAPIが呼ばれる。300ms以内の連続変更は最後の1回のみ実行 | P0 |

#### useCanvasDrag

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-HCD-001 | mousedown でドラッグ開始 | isDragging=true, dragTarget が設定される | P0 |
| FE-HCD-002 | mousemove で座標更新 | dragCurrentX が更新される | P0 |
| FE-HCD-003 | mouseup でドラッグ終了 | isDragging=false。新しいx位置が settings に反映される | P0 |
| FE-HCD-004 | BBox外クリックで選択解除 | BBox外のmousedownでは dragTarget=null | P1 |
| FE-HCD-005 | ドラッグ中のCanvas座標変換 | マウス座標がCanvas内座標に正しく変換される | P1 |

#### useHealthCheck

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-HHC-001 | 初期化時にヘルスチェック実行 | GET /api/health が呼ばれる。serverStatus がセットされる | P0 |
| FE-HHC-002 | サーバー未起動時 | connected=false。エラーメッセージが表示される | P0 |
| FE-HHC-003 | rembg未ロード時 | rembgLoaded=false が検出される | P1 |

#### useDebounce

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-HDB-001 | 値変更後デバウンス時間経過で反映 | 300ms 後に debouncedValue が更新される | P0 |
| FE-HDB-002 | 連続変更でリセット | 300ms以内の連続変更で timer がリセットされ、最後の値のみ反映 | P0 |
| FE-HDB-003 | アンマウント時のクリーンアップ | コンポーネントアンマウント時にtimerがクリアされる | P1 |

### 3.3 API クライアントテスト

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-API-001 | segment API 正常呼び出し | multipart/form-data でファイルが送信される。レスポンスがパースされる | P0 |
| FE-API-002 | merge API 正常呼び出し | JSON ボディで送信される | P0 |
| FE-API-003 | health API 正常呼び出し | GET リクエストが送信される | P0 |
| FE-API-004 | 400 エラーのハンドリング | ErrorResponse がパースされ AppError に変換される | P0 |
| FE-API-005 | 413 エラーのハンドリング | ファイルサイズ超過エラーとして処理される | P0 |
| FE-API-006 | 404 エラーのハンドリング | セグメントID無効エラーとして処理される | P0 |
| FE-API-007 | 500 エラーのハンドリング | サーバーエラーとして処理される | P1 |
| FE-API-008 | ネットワークエラーのハンドリング | type="network" のエラーが生成される | P0 |

### 3.4 ユーティリティテスト

#### fileValidation.ts

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-VAL-001 | JPEG ファイルの検証 | valid=true が返却される | P0 |
| FE-VAL-002 | PNG ファイルの検証 | valid=true | P0 |
| FE-VAL-003 | WebP ファイルの検証 | valid=true | P0 |
| FE-VAL-004 | PDF ファイルの検証 | valid=false。エラーメッセージ付き | P0 |
| FE-VAL-005 | 20MB超ファイルの検証 | valid=false。サイズ超過エラー | P0 |
| FE-VAL-006 | 20MB以下ファイルの検証 | サイズバリデーション通過 | P0 |

#### downloadUtils.ts

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-UTL-001 | base64からBlobへの変換 | 正しいMIMEタイプのBlobが生成される | P0 |
| FE-UTL-002 | ファイル名のタイムスタンプ生成 | merged_{timestamp}.png 形式のファイル名が生成される | P0 |
| FE-UTL-003 | ダウンロードトリガー | a要素のclick()が呼ばれる | P0 |

### 3.5 統合テスト（フロントエンド内）

| ID | テストケース | 期待結果 | 優先度 |
|----|------------|---------|--------|
| FE-INT-001 | 写真入力 → セグメンテーション → プレビュー表示フロー | IDLE → ONE_UPLOADED → SEGMENTING → PREVIEW の状態遷移が正しく行われる | P0 |
| FE-INT-002 | パラメータ変更 → プレビュー更新 | 設定変更後にデバウンス経過で新しいプレビューが表示される | P0 |
| FE-INT-003 | ダウンロード → COMPLETE遷移 | ダウンロード成功後に COMPLETE 状態になる | P0 |
| FE-INT-004 | リセット → IDLE遷移 | リセットボタンで全状態がクリアされ IDLE に戻る | P0 |
| FE-INT-005 | エラー → リトライフロー | エラー発生後にリトライボタンで再実行される | P1 |
| FE-INT-006 | サーバー未起動時の初期表示 | ヘルスチェック失敗時に接続エラーメッセージが表示される | P0 |

---

## 4. E2Eテスト（テストシナリオ）

### 4.1 メインフロー

| ID | テストシナリオ | ステップ | 期待結果 | 優先度 |
|----|------------|---------|---------|--------|
| E2E-001 | 写真2枚入力 → 自動合成 → プレビュー表示 | 1. アプリにアクセス 2. 写真1をドロップゾーン1にドロップ 3. 写真2をドロップゾーン2にドロップ 4. セグメンテーション完了を待つ | プレビューCanvasに合成画像が表示される。2人の人物が左右に配置されている | P0 |
| E2E-002 | パラメータ変更 → プレビュー更新 | 1. E2E-001の状態から開始 2. 背景色を赤(#FF0000)に変更 3. 300ms待機 | プレビュー画像が赤背景に更新される | P0 |
| E2E-003 | スケールスライダー操作 → プレビュー更新 | 1. E2E-001の状態から 2. 人物1のスケールを150%に変更 | プレビューで人物1が拡大表示される | P1 |
| E2E-004 | 影ON/OFF → プレビュー更新 | 1. E2E-001の状態から 2. 影をOFFに切り替え | プレビューから影が消える | P1 |
| E2E-005 | ダウンロード → PNG保存 | 1. E2E-001の状態から 2. ダウンロードボタンをクリック 3. 処理完了を待つ | ブラウザのダウンロードが開始される。ファイル名が merged_*.png | P0 |
| E2E-006 | リセット → 初期状態復帰 | 1. E2E-001の状態から 2. リセットボタンをクリック | 2つの空のドロップゾーンが表示され、初期状態に戻る | P0 |
| E2E-007 | 出力サイズプリセット変更 | 1. E2E-001の状態から 2. 横長(1280x720)を選択 3. ダウンロード | 出力画像が1280x720サイズ | P1 |

### 4.2 エラーフロー

| ID | テストシナリオ | ステップ | 期待結果 | 優先度 |
|----|------------|---------|---------|--------|
| E2E-008 | 非画像ファイルのドロップ | 1. PDFファイルをドロップ | エラーメッセージ表示。再入力可能 | P0 |
| E2E-009 | 大きすぎるファイルのドロップ | 1. 25MBの画像ファイルをドロップ | エラーメッセージ表示。再入力可能 | P0 |
| E2E-010 | サーバー未起動でのアプリ表示 | 1. バックエンド未起動でアプリにアクセス | 「サーバーに接続できません」メッセージが表示される | P0 |

### 4.3 ドラッグ操作フロー

| ID | テストシナリオ | ステップ | 期待結果 | 優先度 |
|----|------------|---------|---------|--------|
| E2E-011 | Canvas上で人物をドラッグ | 1. E2E-001の状態から 2. 人物1をCanvas上で右にドラッグ 3. ドロップ | 人物1が移動した位置で新しいプレビューが表示される | P1 |

---

## 5. テストデータ・フィクスチャ

### 5.1 バックエンド テストフィクスチャ (conftest.py)

```python
# テスト用画像データ
@pytest.fixture
def sample_jpeg_image():
    """300x400のテスト用JPEG画像（人物シルエット付き）"""

@pytest.fixture
def sample_png_image():
    """300x400のテスト用PNG画像"""

@pytest.fixture
def sample_webp_image():
    """300x400のテスト用WebP画像"""

@pytest.fixture
def large_image():
    """5000x3000のテスト用画像（リサイズ検証用）"""

@pytest.fixture
def oversized_file():
    """21MBのダミーファイル（サイズ超過検証用）"""

@pytest.fixture
def non_image_file():
    """テキストファイル（形式検証用）"""

@pytest.fixture
def landscape_image():
    """人物が写っていない風景画像（セグメンテーション失敗検証用）"""

@pytest.fixture
def segmented_pair(client):
    """2枚のセグメンテーション済み画像（merge テスト用）"""

@pytest.fixture
def app_client():
    """httpx AsyncClient (FastAPI TestClient)"""
```

### 5.2 フロントエンド テストフィクスチャ

```typescript
// モック画像ファイル
const createMockFile = (name: string, size: number, type: string): File => ...

// モックAPI レスポンス
const mockSegmentResponse: SegmentResponse = {
  id: "seg_test1234",
  segmented_image: "data:image/png;base64,mock...",
  bbox: { x: 50, y: 10, width: 200, height: 400 },
  foot_y: 410,
  original_size: { width: 300, height: 400 },
  processing_time_ms: 1500,
};

const mockMergeResponse: MergeResponse = {
  merged_image: "data:image/jpeg;base64,mock...",
  processing_time_ms: 150,
  output_size: { width: 512, height: 512 },
};

const mockHealthResponse: HealthResponse = {
  status: "ok",
  rembg_loaded: true,
  version: "2.0.0",
};
```

---

## 6. テスト実行コマンド

### バックエンド

```bash
cd backend/

# 全テスト実行
pytest -v

# カバレッジ付き
pytest --cov=app --cov-report=html --cov-report=term-missing -v

# 特定テストファイル
pytest tests/test_segment.py -v
pytest tests/test_merge.py -v
pytest tests/test_color_correction.py -v
pytest tests/test_shadow_generator.py -v
pytest tests/test_auto_scale.py -v
pytest tests/test_segmentation_store.py -v
pytest tests/test_health.py -v
```

### フロントエンド

```bash
cd frontend/

# 全テスト実行
npx vitest run

# カバレッジ付き
npx vitest run --coverage

# ウォッチモード
npx vitest

# 特定ファイル
npx vitest run src/components/ImageInput/__tests__/
npx vitest run src/hooks/__tests__/
```

---

## 7. テストケース集計

| カテゴリ | テストケース数 |
|---------|-------------|
| バックエンド: POST /api/segment | 18 |
| バックエンド: POST /api/merge | 28 |
| バックエンド: 色調補正 | 6 |
| バックエンド: 影生成 | 6 |
| バックエンド: 自動スケール | 7 |
| バックエンド: アルファマット | 3 |
| バックエンド: SegmentationStore | 6 |
| バックエンド: GET /api/health | 3 |
| バックエンド: ミドルウェア | 5 |
| **バックエンド小計** | **82** |
| フロントエンド: ImageDropzone | 9 |
| フロントエンド: SettingsPanel | 10 |
| フロントエンド: PreviewCanvas | 4 |
| フロントエンド: DownloadButton/ActionBar | 6 |
| フロントエンド: StatusIndicator | 4 |
| フロントエンド: ErrorBoundary | 2 |
| フロントエンド: useSegmentation | 5 |
| フロントエンド: useMerge | 5 |
| フロントエンド: useCanvasDrag | 5 |
| フロントエンド: useHealthCheck | 3 |
| フロントエンド: useDebounce | 3 |
| フロントエンド: APIクライアント | 8 |
| フロントエンド: ユーティリティ | 6 |
| フロントエンド: 統合テスト | 6 |
| **フロントエンド小計** | **76** |
| E2E: メインフロー | 7 |
| E2E: エラーフロー | 3 |
| E2E: ドラッグ操作 | 1 |
| **E2E小計** | **11** |
| **合計** | **169** |

---

## 8. 優先度別テストケース数

| 優先度 | テストケース数 | 説明 |
|--------|-------------|------|
| P0 | 97 | 必須テスト。Phase 3 で 100% 合格必須 |
| P1 | 72 | 重要テスト。カバレッジ目標達成に必要 |
| **合計** | **169** | |
