import type { AppPhase } from "../types/index.ts";

interface DownloadButtonProps {
  phase: AppPhase;
  onDownload: () => void;
  onReset: () => void;
  isMerging: boolean;
}

export function DownloadButton({ phase, onDownload, onReset, isMerging }: DownloadButtonProps) {
  const canDownload = phase === "PREVIEW" || phase === "COMPLETE";

  return (
    <div className="flex gap-3 pt-4 border-t border-gray-200">
      <button
        onClick={onDownload}
        disabled={!canDownload || isMerging}
        className={`
          flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
          font-medium text-sm transition-colors
          ${
            canDownload && !isMerging
              ? "bg-blue-600 text-white hover:bg-blue-700"
              : "bg-gray-200 text-gray-400 cursor-not-allowed"
          }
        `}
      >
        {isMerging ? (
          <>
            <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            合成中...
          </>
        ) : (
          "ダウンロード"
        )}
      </button>

      {phase === "COMPLETE" && (
        <button
          onClick={onReset}
          className="px-4 py-2.5 rounded-lg font-medium text-sm bg-green-600 text-white hover:bg-green-700 transition-colors"
        >
          もう1枚作る
        </button>
      )}

      <button
        onClick={onReset}
        className="px-4 py-2.5 rounded-lg font-medium text-sm border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
      >
        リセット
      </button>
    </div>
  );
}
