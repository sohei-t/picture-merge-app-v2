#!/usr/bin/env python3
"""
自律評価システム - UX最優先版

Phase別worktreeを自動評価し、UXが最も優れたものを選択する

評価軸（合計100%）:
  - ユーザー体験（UX）: 35%
  - 機能完成度: 20%
  - パフォーマンス: 15%
  - テスト品質: 15%
  - セキュリティ: 10%
  - 保守性: 5%
"""

import json
import subprocess
import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from html.parser import HTMLParser
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class UXEvaluationCriteria:
    """UX重視の評価基準"""
    user_experience: float = 0.35   # UX（最優先）
    feature_completeness: float = 0.20  # 機能完成度
    performance: float = 0.15       # パフォーマンス
    test_quality: float = 0.15      # テスト品質
    security: float = 0.10          # セキュリティ
    maintainability: float = 0.05   # 保守性


@dataclass
class WorktreeScore:
    """worktreeの評価スコア"""
    worktree_path: str
    total_score: float
    ux_score: float
    feature_score: float
    performance_score: float
    test_score: float
    security_score: float
    maintainability_score: float
    details: Dict
    ux_breakdown: Dict


class HTMLAnalyzer(HTMLParser):
    """HTML構造を解析してUX評価"""

    def __init__(self):
        super().__init__()
        self.has_nav = False
        self.has_search = False
        self.has_breadcrumb = False
        self.aria_labels = 0
        self.interactive_elements = 0
        self.tabindex_count = 0
        self.forms = 0
        self.buttons = 0
        self.links = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        # ナビゲーション
        if tag == 'nav':
            self.has_nav = True

        # 検索
        if tag == 'input' and attrs_dict.get('type') == 'search':
            self.has_search = True

        # パンくず
        if 'class' in attrs_dict and 'breadcrumb' in attrs_dict['class']:
            self.has_breadcrumb = True

        # アクセシビリティ
        if 'aria-label' in attrs_dict or 'aria-labelledby' in attrs_dict:
            self.aria_labels += 1

        if 'tabindex' in attrs_dict:
            self.tabindex_count += 1

        # インタラクティブ要素
        if tag in ['button', 'a', 'input', 'select', 'textarea']:
            self.interactive_elements += 1

        if tag == 'form':
            self.forms += 1
        if tag == 'button':
            self.buttons += 1
        if tag == 'a':
            self.links += 1


class UXAutonomousEvaluator:
    """UX重視の自律評価システム"""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path)
        self.worktrees_dir = self.project_path / "worktrees"

    def evaluate_user_experience(self, worktree_path: Path) -> Tuple[float, Dict]:
        """
        ユーザー体験（UX）を総合評価（35点満点）

        Returns:
            tuple: (UXスコア, 詳細内訳)
        """
        logger.info("  🎨 Evaluating User Experience...")

        ux_score = 0
        breakdown = {}

        # 1. パフォーマンスUX（10点）
        perf_ux = self._evaluate_performance_ux(worktree_path)
        ux_score += perf_ux
        breakdown['performance_ux'] = perf_ux

        # 2. 直感性・使いやすさ（10点）
        usability = self._evaluate_usability(worktree_path)
        ux_score += usability
        breakdown['usability'] = usability

        # 3. アクセシビリティ（8点）
        accessibility = self._evaluate_accessibility(worktree_path)
        ux_score += accessibility
        breakdown['accessibility'] = accessibility

        # 4. レスポンシブ対応（7点）
        responsive = self._evaluate_responsive_design(worktree_path)
        ux_score += responsive
        breakdown['responsive'] = responsive

        # 100点満点に正規化
        ux_score_normalized = (ux_score / 35) * 100

        logger.info(f"    ✅ UX Score: {ux_score_normalized:.1f}/100 (raw: {ux_score:.1f}/35)")
        logger.info(f"       Performance UX: {perf_ux:.1f}/10")
        logger.info(f"       Usability: {usability:.1f}/10")
        logger.info(f"       Accessibility: {accessibility:.1f}/8")
        logger.info(f"       Responsive: {responsive:.1f}/7")

        return ux_score_normalized, breakdown

    def _evaluate_performance_ux(self, worktree_path: Path) -> float:
        """パフォーマンスUX評価（10点満点）"""
        score = 0

        # package.jsonでフレームワーク確認
        package_json = worktree_path / "package.json"
        if package_json.exists():
            with open(package_json) as f:
                pkg_data = json.load(f)
                dependencies = pkg_data.get('dependencies', {})

                # 高速フレームワークにボーナス
                if 'next' in dependencies:
                    score += 3  # Next.js（App Router、SSR対応）
                elif 'vite' in pkg_data.get('devDependencies', {}):
                    score += 2  # Vite（高速ビルド）

                # パフォーマンス最適化ライブラリ
                if 'react-lazy-load' in dependencies or 'react-lazyload' in dependencies:
                    score += 1
                if '@vercel/analytics' in dependencies:
                    score += 1

        # HTMLでローディング表示確認
        html_files = list(worktree_path.rglob("*.html"))
        for html_file in html_files[:3]:  # 最初の3ファイルのみチェック
            try:
                with open(html_file, encoding='utf-8') as f:
                    content = f.read().lower()
                    if 'loading' in content or 'spinner' in content:
                        score += 1
                        break
            except:
                pass

        # JSでOptimistic UI確認
        js_files = list(worktree_path.rglob("*.js")) + list(worktree_path.rglob("*.jsx"))
        for js_file in js_files[:5]:
            try:
                with open(js_file, encoding='utf-8') as f:
                    content = f.read()
                    if 'optimistic' in content.lower() or 'useMutation' in content:
                        score += 2
                        break
            except:
                pass

        return min(score, 10)

    def _evaluate_usability(self, worktree_path: Path) -> float:
        """使いやすさ評価（10点満点）"""
        score = 0

        html_files = list(worktree_path.rglob("*.html"))

        if not html_files:
            return 5.0  # HTMLがない場合（CLI等）は中間スコア

        for html_file in html_files[:5]:  # 最大5ファイルチェック
            try:
                with open(html_file, encoding='utf-8') as f:
                    content = f.read()

                    analyzer = HTMLAnalyzer()
                    analyzer.feed(content)

                    # ナビゲーション
                    if analyzer.has_nav:
                        score += 2
                    if analyzer.has_search:
                        score += 1
                    if analyzer.has_breadcrumb:
                        score += 1

                    # インタラクティブ要素の充実度
                    if analyzer.buttons > 3:
                        score += 1
                    if analyzer.forms > 0:
                        score += 1

                    # 最初のHTMLで評価完了
                    break

            except Exception as e:
                logger.warning(f"      ⚠️ Error analyzing {html_file.name}: {e}")

        # JSでエラーハンドリング確認
        js_files = list(worktree_path.rglob("*.js")) + list(worktree_path.rglob("*.jsx"))
        for js_file in js_files[:5]:
            try:
                with open(js_file, encoding='utf-8') as f:
                    content = f.read()

                    # try-catch
                    if 'try {' in content and 'catch' in content:
                        score += 1

                    # ユーザーフレンドリーなエラー表示
                    if any(word in content for word in ['toast', 'notification', 'alert', 'snackbar']):
                        score += 2
                        break

            except:
                pass

        return min(score, 10)

    def _evaluate_accessibility(self, worktree_path: Path) -> float:
        """アクセシビリティ評価（8点満点）"""
        score = 0

        html_files = list(worktree_path.rglob("*.html"))

        if not html_files:
            return 4.0  # HTMLがない場合は中間スコア

        for html_file in html_files[:5]:
            try:
                with open(html_file, encoding='utf-8') as f:
                    content = f.read()

                    analyzer = HTMLAnalyzer()
                    analyzer.feed(content)

                    # ARIA属性
                    if analyzer.aria_labels > 5:
                        score += 3
                    elif analyzer.aria_labels > 0:
                        score += 1

                    # キーボードナビゲーション
                    if analyzer.tabindex_count > analyzer.interactive_elements * 0.3:
                        score += 3
                    elif analyzer.tabindex_count > 0:
                        score += 1

                    # セマンティックHTML
                    if '<main>' in content or '<article>' in content or '<section>' in content:
                        score += 2

                    break

            except Exception as e:
                logger.warning(f"      ⚠️ Error analyzing accessibility: {e}")

        return min(score, 8)

    def _evaluate_responsive_design(self, worktree_path: Path) -> float:
        """レスポンシブ対応評価（7点満点）"""
        score = 0

        # CSSでメディアクエリ確認
        css_files = list(worktree_path.rglob("*.css"))
        for css_file in css_files[:5]:
            try:
                with open(css_file, encoding='utf-8') as f:
                    content = f.read()

                    # メディアクエリの数
                    media_queries = content.count('@media')
                    if media_queries >= 3:
                        score += 4
                    elif media_queries > 0:
                        score += 2

                    # Flexbox/Grid
                    if 'display: flex' in content or 'display: grid' in content:
                        score += 2

                    break

            except:
                pass

        # HTMLでviewport meta確認
        html_files = list(worktree_path.rglob("*.html"))
        for html_file in html_files[:1]:
            try:
                with open(html_file, encoding='utf-8') as f:
                    content = f.read()
                    if 'viewport' in content and 'width=device-width' in content:
                        score += 1
                        break
            except:
                pass

        return min(score, 7)

    def evaluate_feature_completeness(self, worktree_path: Path) -> float:
        """機能完成度評価（0-100）"""
        logger.info("  ✨ Evaluating Feature Completeness...")

        score = 70.0  # ベーススコア

        # REQUIREMENTS.mdがあれば、実装率を確認
        requirements_file = worktree_path / "REQUIREMENTS.md"
        if requirements_file.exists():
            try:
                with open(requirements_file, encoding='utf-8') as f:
                    content = f.read()

                    # チェックボックスの実装率
                    total_features = content.count('- [ ]') + content.count('- [x]')
                    completed_features = content.count('- [x]')

                    if total_features > 0:
                        completion_rate = (completed_features / total_features) * 100
                        score = completion_rate
                        logger.info(f"    ✅ Feature completion: {completion_rate:.1f}% ({completed_features}/{total_features})")
                    else:
                        logger.info("    ⚠️ No feature checklist found")

            except Exception as e:
                logger.warning(f"    ⚠️ Error reading REQUIREMENTS.md: {e}")
        else:
            # ファイル数で推定
            src_files = list((worktree_path / "src").rglob("*")) if (worktree_path / "src").exists() else []
            if len(src_files) > 10:
                score = 85.0
            elif len(src_files) > 5:
                score = 75.0

        logger.info(f"    ✅ Feature Score: {score:.1f}/100")
        return score

    def evaluate_performance(self, worktree_path: Path) -> float:
        """パフォーマンス評価（0-100）"""
        logger.info("  ⚡ Evaluating Performance...")

        try:
            benchmark_file = worktree_path / "benchmark-results.json"

            if benchmark_file.exists():
                with open(benchmark_file) as f:
                    bench_data = json.load(f)
                    avg_response_time = bench_data.get('avg_response_time_ms', 1000)

                    if avg_response_time <= 100:
                        score = 100
                    elif avg_response_time >= 1000:
                        score = 0
                    else:
                        score = 100 - ((avg_response_time - 100) / 9)

                    logger.info(f"    ✅ Performance: {score:.1f}/100 (avg: {avg_response_time}ms)")
                    return score
            else:
                logger.info("    ⚠️ No benchmark results, using default score")
                return 75.0

        except Exception as e:
            logger.warning(f"    ⚠️ Performance evaluation failed: {e}")
            return 75.0

    def evaluate_test_quality(self, worktree_path: Path) -> float:
        """テスト品質評価（0-100）"""
        logger.info("  🧪 Evaluating Test Quality...")

        try:
            # テスト実行
            result = subprocess.run(
                ["npm", "test", "--", "--json", "--passWithNoTests"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode == 0 or "passWithNoTests" in result.stdout:
                try:
                    test_data = json.loads(result.stdout)
                    total = test_data.get('numTotalTests', 0)
                    passed = test_data.get('numPassedTests', 0)

                    if total > 0:
                        pass_rate = (passed / total) * 100
                        logger.info(f"    ✅ Test Quality: {pass_rate:.1f}% ({passed}/{total})")
                        return pass_rate
                    else:
                        logger.info("    ⚠️ No tests found")
                        return 50.0
                except json.JSONDecodeError:
                    logger.info("    ⚠️ Test output parsing failed")
                    return 70.0
            else:
                logger.warning(f"    ⚠️ Tests failed")
                return 0.0

        except subprocess.TimeoutExpired:
            logger.warning("    ⚠️ Test execution timeout")
            return 50.0
        except Exception as e:
            logger.warning(f"    ⚠️ Test evaluation failed: {e}")
            return 70.0

    def evaluate_security(self, worktree_path: Path) -> float:
        """セキュリティ評価（0-100）"""
        logger.info("  🔐 Evaluating Security...")

        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.stdout:
                audit_data = json.loads(result.stdout)
                vulnerabilities = audit_data.get('metadata', {}).get('vulnerabilities', {})

                critical = vulnerabilities.get('critical', 0)
                high = vulnerabilities.get('high', 0)
                moderate = vulnerabilities.get('moderate', 0)
                low = vulnerabilities.get('low', 0)

                score = 100 - (critical * 20 + high * 10 + moderate * 5 + low * 2)
                score = max(0, score)

                logger.info(f"    ✅ Security: {score:.1f}/100 (C:{critical}, H:{high}, M:{moderate}, L:{low})")
                return score
            else:
                logger.info("    ⚠️ No npm audit data")
                return 85.0

        except Exception as e:
            logger.warning(f"    ⚠️ Security evaluation failed: {e}")
            return 85.0

    def evaluate_maintainability(self, worktree_path: Path) -> float:
        """保守性評価（0-100）"""
        logger.info("  🔧 Evaluating Maintainability...")

        try:
            src_dir = worktree_path / "src"
            if not src_dir.exists():
                return 70.0

            total_lines = 0
            for file in src_dir.rglob("*.js"):
                with open(file, encoding='utf-8') as f:
                    total_lines += len(f.readlines())
            for file in src_dir.rglob("*.ts"):
                with open(file, encoding='utf-8') as f:
                    total_lines += len(f.readlines())

            # 1000行以下なら満点、5000行以上なら0点
            if total_lines <= 1000:
                score = 100
            elif total_lines >= 5000:
                score = 30
            else:
                score = 100 - ((total_lines - 1000) / 40)

            logger.info(f"    ✅ Maintainability: {score:.1f}/100 (lines: {total_lines})")
            return max(30, score)

        except Exception as e:
            logger.warning(f"    ⚠️ Maintainability evaluation failed: {e}")
            return 70.0

    def evaluate_worktree(
        self,
        worktree_path: Path,
        criteria: UXEvaluationCriteria
    ) -> WorktreeScore:
        """worktreeを総合評価（UX重視）"""

        logger.info(f"\n📊 Evaluating: {worktree_path.name}")
        logger.info("=" * 60)

        # 各項目を評価
        ux_score, ux_breakdown = self.evaluate_user_experience(worktree_path)
        feature_score = self.evaluate_feature_completeness(worktree_path)
        perf_score = self.evaluate_performance(worktree_path)
        test_score = self.evaluate_test_quality(worktree_path)
        security_score = self.evaluate_security(worktree_path)
        maintainability_score = self.evaluate_maintainability(worktree_path)

        # 加重平均で総合スコア計算
        total_score = (
            ux_score * criteria.user_experience +
            feature_score * criteria.feature_completeness +
            perf_score * criteria.performance +
            test_score * criteria.test_quality +
            security_score * criteria.security +
            maintainability_score * criteria.maintainability
        )

        result = WorktreeScore(
            worktree_path=str(worktree_path),
            total_score=total_score,
            ux_score=ux_score,
            feature_score=feature_score,
            performance_score=perf_score,
            test_score=test_score,
            security_score=security_score,
            maintainability_score=maintainability_score,
            details={
                "user_experience": f"{ux_score:.1f}",
                "feature_completeness": f"{feature_score:.1f}",
                "performance": f"{perf_score:.1f}",
                "test_quality": f"{test_score:.1f}",
                "security": f"{security_score:.1f}",
                "maintainability": f"{maintainability_score:.1f}"
            },
            ux_breakdown=ux_breakdown
        )

        logger.info(f"\n✅ Total Score: {total_score:.1f}/100")
        logger.info(f"   UX (35%): {ux_score:.1f} × 0.35 = {ux_score * 0.35:.1f}")
        logger.info(f"   Feature (20%): {feature_score:.1f} × 0.20 = {feature_score * 0.20:.1f}")
        logger.info(f"   Performance (15%): {perf_score:.1f} × 0.15 = {perf_score * 0.15:.1f}")
        logger.info(f"   Test Quality (15%): {test_score:.1f} × 0.15 = {test_score * 0.15:.1f}")
        logger.info(f"   Security (10%): {security_score:.1f} × 0.10 = {security_score * 0.10:.1f}")
        logger.info(f"   Maintainability (5%): {maintainability_score:.1f} × 0.05 = {maintainability_score * 0.05:.1f}")
        logger.info("=" * 60)

        return result

    def select_best_worktree(
        self,
        worktree_names: List[str],
        criteria: Optional[UXEvaluationCriteria] = None
    ) -> Tuple[str, WorktreeScore]:
        """複数のworktreeから最良を自動選択（UX重視）"""

        if criteria is None:
            criteria = UXEvaluationCriteria()

        results = {}

        logger.info("\n🚀 Starting UX-focused autonomous evaluation...")
        logger.info(f"📋 Evaluating {len(worktree_names)} worktrees")
        logger.info("\n📊 Evaluation Criteria:")
        logger.info(f"   User Experience (UX): {criteria.user_experience * 100:.0f}%")
        logger.info(f"   Feature Completeness: {criteria.feature_completeness * 100:.0f}%")
        logger.info(f"   Performance: {criteria.performance * 100:.0f}%")
        logger.info(f"   Test Quality: {criteria.test_quality * 100:.0f}%")
        logger.info(f"   Security: {criteria.security * 100:.0f}%")
        logger.info(f"   Maintainability: {criteria.maintainability * 100:.0f}%")

        for wt_name in worktree_names:
            wt_path = self.worktrees_dir / wt_name
            if wt_path.exists():
                score_result = self.evaluate_worktree(wt_path, criteria)
                results[wt_name] = score_result
            else:
                logger.warning(f"⚠️ Worktree not found: {wt_name}")

        if not results:
            raise ValueError("No valid worktrees found for evaluation")

        # 最高スコアを選択
        best_name = max(results, key=lambda k: results[k].total_score)
        best_score = results[best_name]

        logger.info("\n" + "=" * 60)
        logger.info("🏆 EVALUATION RESULTS (UX-Focused)")
        logger.info("=" * 60)

        for name, score in sorted(results.items(), key=lambda x: x[1].total_score, reverse=True):
            logger.info(f"\n{name}:")
            logger.info(f"  Total: {score.total_score:.1f}/100")
            logger.info(f"  UX: {score.ux_score:.1f}, Feature: {score.feature_score:.1f}, Perf: {score.performance_score:.1f}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ SELECTED: " + best_name)
        logger.info(f"   Total Score: {best_score.total_score:.1f}/100")
        logger.info(f"   UX Score: {best_score.ux_score:.1f}/100 (35% weight)")
        logger.info("=" * 60)

        # 結果をJSONで保存
        report_path = self.project_path / "EVALUATION_REPORT_UX.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "selected": best_name,
                "evaluation_type": "UX-Focused",
                "results": {
                    name: {
                        "total_score": score.total_score,
                        "scores": score.details,
                        "ux_breakdown": score.ux_breakdown
                    }
                    for name, score in results.items()
                },
                "criteria": {
                    "user_experience": criteria.user_experience,
                    "feature_completeness": criteria.feature_completeness,
                    "performance": criteria.performance,
                    "test_quality": criteria.test_quality,
                    "security": criteria.security,
                    "maintainability": criteria.maintainability
                }
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"\n📄 UX Evaluation report saved: {report_path}")

        return best_name, best_score

    def merge_to_main_and_sync(self, selected_worktree: str, phase: str = None, skip_file_check: bool = False) -> bool:
        """選択されたworktreeをmainにマージし、他のworktreeに同期

        Args:
            selected_worktree: 選択されたworktree名（例: "phase2-impl-prototype-a"）
            phase: フェーズ名（例: "phase2"）- 自動判定も可能
            skip_file_check: 重要ファイルチェックをスキップするか

        Returns:
            bool: 成功したらTrue
        """
        try:
            # フェーズを自動判定
            if phase is None:
                if 'phase1' in selected_worktree:
                    phase = 'phase1'
                elif 'phase2' in selected_worktree:
                    phase = 'phase2'
                elif 'phase4' in selected_worktree:
                    phase = 'phase4'

            logger.info("\n" + "=" * 60)
            logger.info(f"🔄 Merging {selected_worktree} to main...")
            logger.info("=" * 60)

            # ブランチ名を推定（worktree名からphaseN-プレフィックスを除去）
            branch_name = selected_worktree
            for prefix in ['phase1-', 'phase2-', 'phase3-', 'phase4-', 'phase5-']:
                branch_name = branch_name.replace(prefix, 'phase/')

            # mainにマージ（M4 Mac対応）
            git_cmd = '/usr/bin/git' if os.path.exists('/usr/bin/git') else 'git'
            subprocess.run(
                [git_cmd, 'merge', '--no-edit', branch_name],
                cwd=self.project_path,
                check=True
            )
            logger.info(f"✅ Merged {branch_name} to main")

            # Phase別の重要ファイル確認（skip_file_check=Trueの場合はスキップ）
            if not skip_file_check:
                # Phase別に確認すべきファイルを定義
                phase_required_files = {
                    'phase1': {
                        'required': ['REQUIREMENTS.md', 'SPEC.md'],
                        'optional': ['IMAGE_PROMPTS.json', 'AUDIO_PROMPTS.json', 'TECH_STACK.md', 'WBS.json']
                    },
                    'phase2': {
                        'required': ['src/', 'index.html'],
                        'optional': ['tests/', 'assets/']
                    },
                    'phase4': {
                        'required': [],
                        'optional': ['benchmark-results.json', 'coverage/']
                    }
                }

                if phase in phase_required_files:
                    config = phase_required_files[phase]
                    missing_required = []
                    missing_optional = []

                    for file in config.get('required', []):
                        file_path = self.project_path / file
                        if file_path.exists():
                            logger.info(f"  ✅ {file} - 存在確認（必須）")
                        else:
                            missing_required.append(file)
                            logger.error(f"  ❌ {file} - 必須ファイルが見つかりません")

                    for file in config.get('optional', []):
                        file_path = self.project_path / file
                        if file_path.exists():
                            logger.info(f"  ✅ {file} - 存在確認（オプション）")
                        else:
                            missing_optional.append(file)
                            logger.info(f"  ℹ️  {file} - オプションファイル（未生成）")

                    if missing_required:
                        logger.error(f"\n❌ 必須ファイルが不足しています: {', '.join(missing_required)}")
                        logger.error("   → このPhaseの成果物が不完全です。再実行を検討してください。")

                    if missing_optional:
                        logger.info(f"\nℹ️  オプションファイル（後続Phaseで生成予定）: {', '.join(missing_optional)}")

            # すべてのworktreeに同期
            logger.info("\n🔄 Syncing to all worktrees...")
            sync_success = 0
            sync_failed = 0

            if self.worktrees_dir.exists():
                for worktree in self.worktrees_dir.iterdir():
                    if worktree.is_dir() and worktree.name != selected_worktree:
                        try:
                            # git merge main を各worktreeで実行
                            subprocess.run(
                                [git_cmd, 'merge', '--no-edit', 'main'],
                                cwd=worktree,
                                check=True,
                                capture_output=True
                            )
                            logger.info(f"  ✅ Synced to {worktree.name}")
                            sync_success += 1
                        except subprocess.CalledProcessError:
                            logger.warning(f"  ⚠️  Failed to sync to {worktree.name}")
                            sync_failed += 1

            logger.info(f"\n✅ Merge and sync completed! (Success: {sync_success}, Failed: {sync_failed})")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Merge failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return False


def main():
    """CLI エントリーポイント"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 autonomous_evaluator_ux.py <project_path> [worktree1] [worktree2] ... [options]")
        print("\nOptions:")
        print("  --auto-merge         選択されたworktreeを自動でmainにマージし全worktreeに同期")
        print("  --skip-file-check    Phase別の重要ファイルチェックをスキップ")
        print("  --phase=<phase>      フェーズを明示的に指定（phase1, phase2, phase4）")
        print("\nExample:")
        print("  python3 autonomous_evaluator_ux.py . phase2-impl-prototype-a phase2-impl-prototype-b phase2-impl-prototype-c")
        print("  python3 autonomous_evaluator_ux.py . phase2-impl-prototype-a phase2-impl-prototype-b --auto-merge")
        sys.exit(1)

    # オプションを抽出
    args = sys.argv[1:]
    options = [a for a in args if a.startswith('--')]
    non_options = [a for a in args if not a.startswith('--')]

    project_path = Path(non_options[0]) if non_options else Path('.')
    worktree_names = non_options[1:] if len(non_options) > 1 else []

    # オプション解析
    auto_merge = '--auto-merge' in options
    skip_file_check = '--skip-file-check' in options
    phase = None
    for opt in options:
        if opt.startswith('--phase='):
            phase = opt.split('=')[1]

    # worktree_namesからオプションを除外
    worktree_names = [w for w in worktree_names if not w.startswith('--')]

    if not worktree_names:
        # worktrees/配下の全フォルダを評価
        worktrees_dir = project_path / "worktrees"
        if worktrees_dir.exists():
            worktree_names = [d.name for d in worktrees_dir.iterdir() if d.is_dir()]

    evaluator = UXAutonomousEvaluator(project_path)
    best_name, best_score = evaluator.select_best_worktree(worktree_names)

    print(f"\n🎉 Best worktree (UX-focused): {best_name}")
    print(f"   Total score: {best_score.total_score:.1f}/100")
    print(f"   UX score: {best_score.ux_score:.1f}/100")

    # 自動マージ・同期（--auto-mergeオプション）
    if auto_merge:
        print("\n🔄 Auto-merge enabled - merging to main and syncing...")
        if skip_file_check:
            print("ℹ️  File check skipped (--skip-file-check)")
        evaluator.merge_to_main_and_sync(best_name, phase=phase, skip_file_check=skip_file_check)


if __name__ == "__main__":
    main()
