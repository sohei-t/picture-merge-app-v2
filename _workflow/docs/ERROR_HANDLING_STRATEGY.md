# 🛡️ エラーハンドリング戦略

## 🎯 目的

エージェント実行中のエラーを自動的に検出・回復し、人間の介入を最小限に抑える。

## 🔄 3段階エラーリカバリシステム

### Level 1: 自動リトライ（軽微なエラー）

```yaml
auto_retry:
  trigger_conditions:
    - network_timeout
    - temporary_file_lock
    - api_rate_limit
    - memory_limit_exceeded

  strategy:
    max_attempts: 3
    backoff: exponential  # 1秒 → 2秒 → 4秒

  implementation:
    ```python
    def retry_with_backoff(task, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                return task.execute()
            except TemporaryError as e:
                if attempt == max_attempts - 1:
                    raise
                wait_time = 2 ** attempt
                log.warning(f"Retry {attempt + 1}/{max_attempts} after {wait_time}s")
                time.sleep(wait_time)
    ```
```

### Level 2: フォールバック戦略（中程度のエラー）

```yaml
fallback_strategy:
  trigger_conditions:
    - test_failure_after_retries
    - dependency_not_available
    - resource_exhausted
    - partial_implementation_failure

  strategies:
    simplified_approach:
      description: "より単純な実装にフォールバック"
      example: "高度なアニメーション → 基本的な遷移"

    alternative_tool:
      description: "代替ツールを使用"
      example: "npm → yarn, puppeteer → playwright"

    graceful_degradation:
      description: "機能を段階的に削減"
      example: "リアルタイム同期 → 定期同期 → 手動同期"

  implementation:
    ```python
    def execute_with_fallback(primary_task, fallback_tasks):
        try:
            return primary_task.execute()
        except RecoverableError as e:
            log.warning(f"Primary failed: {e}, trying fallbacks")
            for fallback in fallback_tasks:
                try:
                    result = fallback.execute()
                    log.info(f"Fallback succeeded: {fallback.name}")
                    return result
                except:
                    continue
            raise FallbackExhaustedError()
    ```
```

### Level 3: ロールバック＆通知（重大なエラー）

```yaml
rollback_and_notify:
  trigger_conditions:
    - critical_test_failure
    - security_vulnerability_detected
    - data_corruption
    - unrecoverable_state

  actions:
    immediate:
      - stop_all_agents
      - save_current_state
      - rollback_to_last_checkpoint

    notification:
      - log_detailed_error
      - create_error_report
      - suggest_manual_fixes

    recovery_suggestions:
      - "前のコミットに戻す: git reset --hard HEAD~1"
      - "worktreeを作り直す: git worktree remove && git worktree add"
      - "依存関係をクリア: rm -rf node_modules && npm install"

  implementation:
    ```python
    def handle_critical_error(error, context):
        # 1. 即座に停止
        stop_all_running_tasks()

        # 2. 状態を保存
        checkpoint = save_current_state(context)

        # 3. ロールバック
        rollback_to_checkpoint(checkpoint.previous)

        # 4. 詳細レポート生成
        report = generate_error_report(error, context, checkpoint)

        # 5. ユーザーに通知
        notify_user(report, recovery_suggestions)
    ```
```

## 🔍 エラー検出メカニズム

### リアルタイム監視

```yaml
monitoring:
  health_checks:
    interval: 30s
    checks:
      - agent_heartbeat
      - memory_usage < 80%
      - disk_space > 1GB
      - network_connectivity

  progress_tracking:
    - task_completion_rate
    - error_frequency
    - retry_count
    - execution_time_vs_estimate

  anomaly_detection:
    - sudden_spike_in_errors
    - unusual_execution_time
    - repeated_same_error
    - resource_usage_pattern
```

### エラーパターン認識

```yaml
error_patterns:
  import_error:
    pattern: "Cannot find module|ModuleNotFoundError"
    solution: "npm install または pip install"
    auto_fix: true

  syntax_error:
    pattern: "SyntaxError|Unexpected token"
    solution: "構文チェックと自動修正"
    auto_fix: true

  type_error:
    pattern: "TypeError|is not a function"
    solution: "型定義の確認と修正"
    auto_fix: false

  test_failure:
    pattern: "Test failed|FAIL"
    solution: "テストコードまたは実装の修正"
    auto_fix: true
```

## 🚦 エラー優先度マトリックス

| エラータイプ | 影響度 | 頻度 | 対応 | 自動修復 |
|------------|--------|------|------|----------|
| ネットワークタイムアウト | 低 | 中 | リトライ | ✅ |
| 構文エラー | 中 | 高 | 自動修正 | ✅ |
| テスト失敗 | 中 | 高 | 修正ループ | ✅ |
| 依存関係エラー | 高 | 中 | インストール | ✅ |
| メモリ不足 | 高 | 低 | リソース解放 | ✅ |
| セキュリティ脆弱性 | 最高 | 低 | 即座停止 | ❌ |
| データ破損 | 最高 | 極低 | ロールバック | ❌ |

## 📝 エラーログフォーマット

```json
{
  "timestamp": "2024-12-10T10:30:00Z",
  "phase": "implementation",
  "agent": "frontend_developer",
  "task_id": "FE001",
  "error": {
    "type": "TestFailure",
    "message": "3 tests failed",
    "stack": "...",
    "severity": "medium"
  },
  "context": {
    "file": "src/components/Button.test.js",
    "line": 42,
    "previous_attempts": 2
  },
  "recovery": {
    "strategy": "auto_fix",
    "action": "modify_implementation",
    "success": true
  }
}
```

## 🔧 実装例

### エラーハンドラーの統合

```python
class WorkflowErrorHandler:
    def __init__(self):
        self.retry_count = {}
        self.error_history = []

    def handle_error(self, error, context):
        # エラータイプを判定
        error_level = self.classify_error(error)

        if error_level == "minor":
            return self.level1_retry(error, context)
        elif error_level == "moderate":
            return self.level2_fallback(error, context)
        else:
            return self.level3_rollback(error, context)

    def classify_error(self, error):
        if isinstance(error, (NetworkError, TimeoutError)):
            return "minor"
        elif isinstance(error, (TestFailure, DependencyError)):
            return "moderate"
        else:
            return "critical"

    def level1_retry(self, error, context, max_retries=3):
        task_id = context.task_id
        self.retry_count[task_id] = self.retry_count.get(task_id, 0) + 1

        if self.retry_count[task_id] <= max_retries:
            wait_time = 2 ** (self.retry_count[task_id] - 1)
            time.sleep(wait_time)
            return "retry"
        else:
            return self.level2_fallback(error, context)

    def level2_fallback(self, error, context):
        fallback_strategy = self.get_fallback_strategy(error)
        if fallback_strategy:
            return fallback_strategy
        else:
            return self.level3_rollback(error, context)

    def level3_rollback(self, error, context):
        self.save_state(context)
        self.rollback_changes(context)
        self.notify_user(error, context)
        return "manual_intervention_required"
```

## 🎯 期待される効果

- **自動回復率**: 95%以上
- **平均復旧時間**: 2分以内
- **人間介入の削減**: 80%
- **エラーからの学習**: パターン蓄積で精度向上

## ✅ 導入チェックリスト

- [ ] エラーハンドラークラスの実装
- [ ] リトライメカニズムの実装
- [ ] フォールバック戦略の定義
- [ ] ロールバック機能の実装
- [ ] エラーログシステムの構築
- [ ] 監視ダッシュボードの設定
- [ ] エラーパターンDBの作成
- [ ] 自動修復スクリプトの準備