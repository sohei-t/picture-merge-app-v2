import { useCallback } from "react";
import type { AdjustParams } from "../types/index.ts";
import { DEFAULT_ADJUST_PARAMS } from "../types/index.ts";

interface EnhancePanelProps {
  target: "person1" | "person2";
  segId: string;
  isEnhancing: boolean;
  isAdjusting: boolean;
  isResetting: boolean;
  isAiEnhanced: boolean;
  adjustParams: AdjustParams;
  onAiEnhance: (segId: string) => void;
  onAdjust: (segId: string, params: AdjustParams) => void;
  onResetToOriginal: (segId: string) => void;
  onClose: () => void;
}

const SLIDERS: { key: keyof AdjustParams; label: string; icon: string }[] = [
  { key: "brightness", label: "明るさ", icon: "☀" },
  { key: "contrast", label: "コントラスト", icon: "◑" },
  { key: "saturation", label: "彩度", icon: "🎨" },
  { key: "temperature", label: "色温度", icon: "🌡" },
  { key: "sharpness", label: "シャープネス", icon: "△" },
];

export function EnhancePanel({
  target,
  segId,
  isEnhancing,
  isAdjusting,
  isResetting,
  isAiEnhanced,
  adjustParams,
  onAiEnhance,
  onAdjust,
  onResetToOriginal,
  onClose,
}: EnhancePanelProps) {
  const label = target === "person1" ? "人物1" : "人物2";

  const handleSliderChange = useCallback(
    (key: keyof AdjustParams, value: number) => {
      const newParams = { ...adjustParams, [key]: value };
      onAdjust(segId, newParams);
    },
    [segId, adjustParams, onAdjust]
  );

  const handleReset = useCallback(() => {
    onAdjust(segId, { ...DEFAULT_ADJUST_PARAMS });
  }, [segId, onAdjust]);

  const isDefault = Object.entries(adjustParams).every(
    ([k, v]) => v === DEFAULT_ADJUST_PARAMS[k as keyof AdjustParams]
  );

  return (
    <div className="border border-blue-300 bg-blue-50 rounded-lg p-3 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-blue-800">
          画質調整 - {label}
        </h4>
        <button
          onClick={onClose}
          className="text-xs text-gray-500 hover:text-red-600 transition-colors"
        >
          閉じる
        </button>
      </div>

      {/* AI Enhancement button */}
      <div>
        <button
          onClick={() => onAiEnhance(segId)}
          disabled={isEnhancing || isAiEnhanced}
          className={`w-full text-sm px-3 py-2 rounded-lg font-medium transition-colors ${
            isAiEnhanced
              ? "bg-green-100 text-green-700 border border-green-300 cursor-default"
              : isEnhancing
              ? "bg-purple-100 text-purple-600 border border-purple-300 cursor-wait"
              : "bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 shadow-sm"
          }`}
        >
          {isEnhancing
            ? "AI高画質化 処理中..."
            : isAiEnhanced
            ? "AI高画質化 適用済み"
            : "AI高画質化（Real-ESRGAN + GFPGAN）"}
        </button>
        {!isAiEnhanced && !isEnhancing && (
          <p className="text-[10px] text-gray-500 mt-1">
            超解像 + 顔復元で鮮明に（初回5-15秒）
          </p>
        )}
      </div>

      {/* Divider */}
      <div className="flex items-center gap-2">
        <div className="flex-1 border-t border-blue-200" />
        <span className="text-[10px] text-blue-400 font-medium">手動調整</span>
        <div className="flex-1 border-t border-blue-200" />
      </div>

      {/* Manual sliders */}
      <div className="space-y-2">
        {SLIDERS.map(({ key, label: sliderLabel, icon }) => (
          <div key={key}>
            <div className="flex items-center justify-between">
              <label className="text-xs text-gray-600">
                {icon} {sliderLabel}
              </label>
              <span className="text-[10px] text-gray-400 tabular-nums w-10 text-right">
                {adjustParams[key] > 0 ? "+" : ""}
                {Math.round(adjustParams[key] * 100)}%
              </span>
            </div>
            <input
              type="range"
              min={-100}
              max={100}
              value={Math.round(adjustParams[key] * 100)}
              onChange={(e) =>
                handleSliderChange(key, Number(e.target.value) / 100)
              }
              className="w-full h-1.5 accent-blue-500"
            />
          </div>
        ))}
      </div>

      {/* Reset sliders button */}
      <button
        onClick={handleReset}
        disabled={isDefault && !isAdjusting}
        className="w-full text-xs px-3 py-1.5 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {isAdjusting ? "適用中..." : "調整をリセット"}
      </button>

      {/* Reset to original button */}
      <div className="pt-1 border-t border-blue-200">
        <button
          onClick={() => onResetToOriginal(segId)}
          disabled={isResetting || isEnhancing}
          className="w-full text-xs px-3 py-1.5 border border-red-300 text-red-600 rounded hover:bg-red-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {isResetting ? "復元中..." : "元の画像に戻す"}
        </button>
        <p className="text-[10px] text-gray-400 mt-0.5 text-center">
          高画質化・消しゴム・調整をすべて取り消します
        </p>
      </div>
    </div>
  );
}
