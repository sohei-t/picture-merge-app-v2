import type { AppPhase, AppError } from "../types/index.ts";

interface StatusIndicatorProps {
  phase: AppPhase;
  error: AppError | null;
  processingTimeMs: number | null;
}

const PHASE_LABELS: Record<AppPhase, string> = {
  IDLE: "写真をアップロードしてください",
  ONE_UPLOADED: "2枚目の写真をアップロードしてください",
  SEGMENTING: "人物を切り抜き中...",
  PREVIEW: "合成プレビュー",
  MERGING: "高解像度で合成中...",
  COMPLETE: "合成完了！",
  ERROR: "エラーが発生しました",
};

const PHASE_COLORS: Record<AppPhase, string> = {
  IDLE: "text-gray-500",
  ONE_UPLOADED: "text-blue-500",
  SEGMENTING: "text-yellow-600",
  PREVIEW: "text-green-600",
  MERGING: "text-yellow-600",
  COMPLETE: "text-green-700",
  ERROR: "text-red-600",
};

export function StatusIndicator({ phase, error, processingTimeMs }: StatusIndicatorProps) {
  return (
    <div className="space-y-1" role="status" aria-live="polite">
      <p className={`text-sm font-medium ${PHASE_COLORS[phase]}`}>
        {phase === "SEGMENTING" || phase === "MERGING" ? (
          <span className="inline-flex items-center gap-1.5">
            <span className="animate-spin inline-block w-3.5 h-3.5 border-2 border-current border-t-transparent rounded-full" />
            {PHASE_LABELS[phase]}
          </span>
        ) : (
          PHASE_LABELS[phase]
        )}
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm">
          <p className="text-red-700 font-medium">{error.message}</p>
          {error.detail && (
            <p className="text-red-500 text-xs mt-1">
              {typeof error.detail === "string" ? error.detail : JSON.stringify(error.detail)}
            </p>
          )}
          {error.retryable && (
            <p className="text-red-400 text-xs mt-1">再試行できます。</p>
          )}
        </div>
      )}

      {processingTimeMs !== null && phase !== "ERROR" && (
        <p className="text-xs text-gray-400">
          処理時間: {(processingTimeMs / 1000).toFixed(2)}秒
        </p>
      )}
    </div>
  );
}
