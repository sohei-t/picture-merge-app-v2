import type { AppPhase } from "../types/index.ts";

interface DownloadButtonProps {
  phase: AppPhase;
  onDownload: () => void;
  onReset: () => void;
  isMerging: boolean;
  isCropMode?: boolean;
  isCropping?: boolean;
  hasCropRect?: boolean;
  onCropToggle?: () => void;
  onCropExecute?: () => void;
}

export function DownloadButton({
  phase,
  onDownload,
  onReset,
  isMerging,
  isCropMode,
  isCropping,
  hasCropRect,
  onCropToggle,
  onCropExecute,
}: DownloadButtonProps) {
  const canDownload = phase === "PREVIEW" || phase === "COMPLETE";

  return (
    <div className="flex flex-wrap gap-3 pt-4 border-t border-gray-200">
      <button
        onClick={onDownload}
        disabled={!canDownload || isMerging || isCropMode}
        className={`
          flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
          font-medium text-sm transition-colors
          ${
            canDownload && !isMerging && !isCropMode
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

      {canDownload && onCropToggle && (
        <>
          <button
            onClick={onCropToggle}
            className={`
              px-4 py-2.5 rounded-lg font-medium text-sm transition-colors
              ${
                isCropMode
                  ? "bg-orange-600 text-white hover:bg-orange-700"
                  : "bg-purple-600 text-white hover:bg-purple-700"
              }
            `}
          >
            {isCropMode ? "トリミング解除" : "トリミング"}
          </button>

          {isCropMode && hasCropRect && onCropExecute && (
            <button
              onClick={onCropExecute}
              disabled={isCropping}
              className={`
                px-4 py-2.5 rounded-lg font-medium text-sm transition-colors
                ${isCropping
                  ? "bg-gray-400 text-white cursor-not-allowed"
                  : "bg-green-600 text-white hover:bg-green-700"
                }
              `}
            >
              {isCropping ? (
                <>
                  <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-1" />
                  高解像度で切り出し中...
                </>
              ) : (
                "切り出しダウンロード（高解像度）"
              )}
            </button>
          )}
        </>
      )}

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
