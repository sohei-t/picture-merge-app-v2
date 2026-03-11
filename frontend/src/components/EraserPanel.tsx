import { useState, useRef, useCallback, useEffect } from "react";
import { createPortal } from "react-dom";
import type { DetectedRegion, SegmentationResult } from "../types/index.ts";
import type { EraserMode } from "../hooks/useEraser.ts";

interface EraserPanelProps {
  mode: EraserMode;
  target: "person1" | "person2" | null;
  person: SegmentationResult | null;
  regions: DetectedRegion[];
  isDetecting: boolean;
  isErasing: boolean;
  brushSize: number;
  onBrushSizeChange: (size: number) => void;
  onAutoDetect: () => void;
  onBrushMode: () => void;
  onEraseRegions: (regionIds: number[]) => void;
  onBrushApply: (
    strokes: { x: number; y: number; radius: number }[],
    displayWidth: number,
    displayHeight: number
  ) => void;
  onClose: () => void;
}

function RegionSelector({
  regions,
  isErasing,
  onErase,
  expanded,
}: {
  regions: DetectedRegion[];
  isErasing: boolean;
  onErase: (regionIds: number[]) => void;
  expanded: boolean;
}) {
  const [selected, setSelected] = useState<Set<number>>(new Set());

  const toggle = (id: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  if (regions.length <= 1) {
    return (
      <div className="text-sm text-gray-500 text-center py-4">
        独立した領域が検出されませんでした。ブラシモードで手動消去してください。
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className={`text-gray-600 ${expanded ? "text-sm" : "text-xs"}`}>
        削除する領域を選択してください（{regions.length}個検出）
      </p>
      <div
        className={`grid gap-2 overflow-y-auto ${
          expanded ? "grid-cols-3 max-h-[400px]" : "grid-cols-2 max-h-[200px]"
        }`}
      >
        {regions.map((r) => (
          <button
            key={r.region_id}
            onClick={() => toggle(r.region_id)}
            className={`relative border-2 rounded-lg p-1 transition-colors ${
              selected.has(r.region_id)
                ? "border-red-500 bg-red-50"
                : "border-gray-200 bg-white hover:border-blue-300"
            }`}
          >
            <img
              src={r.thumbnail}
              alt={`領域${r.region_id + 1}`}
              className={`w-full object-contain ${expanded ? "h-28" : "h-16"}`}
            />
            <span className="absolute top-0.5 left-0.5 text-[9px] bg-black/60 text-white px-1 rounded">
              {r.is_main ? "メイン" : `領域${r.region_id + 1}`}
            </span>
            {selected.has(r.region_id) && (
              <span className="absolute top-0.5 right-0.5 text-red-500 text-sm font-bold">
                x
              </span>
            )}
          </button>
        ))}
      </div>
      <button
        onClick={() => onErase(Array.from(selected))}
        disabled={selected.size === 0 || isErasing}
        className={`w-full bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${
          expanded ? "text-sm px-4 py-2" : "text-xs px-3 py-1.5"
        }`}
      >
        {isErasing ? "消去中..." : `選択した${selected.size}個の領域を削除`}
      </button>
    </div>
  );
}

function BrushCanvas({
  person,
  brushSize,
  isErasing,
  expanded,
  onApply,
}: {
  person: SegmentationResult;
  brushSize: number;
  isErasing: boolean;
  expanded: boolean;
  onApply: (
    strokes: { x: number; y: number; radius: number }[],
    displayWidth: number,
    displayHeight: number
  ) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [strokes, setStrokes] = useState<
    { x: number; y: number; radius: number }[]
  >([]);
  const [isDrawing, setIsDrawing] = useState(false);

  // Calculate display dimensions — changes with expanded
  const maxW = expanded ? 700 : 300;
  const maxH = expanded ? 600 : 300;
  const origW = person.originalSize.width;
  const origH = person.originalSize.height;
  const ratio = Math.min(maxW / origW, maxH / origH, 1);
  const displayW = Math.round(origW * ratio);
  const displayH = Math.round(origH * ratio);

  // Draw: load image then render everything onto the canvas.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = displayW;
    canvas.height = displayH;

    let cancelled = false;
    const img = new window.Image();
    img.onload = () => {
      if (cancelled) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      // Checkerboard
      const pat = expanded ? 12 : 8;
      for (let py = 0; py < displayH; py += pat) {
        for (let px = 0; px < displayW; px += pat) {
          ctx.fillStyle =
            (Math.floor(px / pat) + Math.floor(py / pat)) % 2 === 0
              ? "#e5e7eb"
              : "#ffffff";
          ctx.fillRect(px, py, pat, pat);
        }
      }

      ctx.drawImage(img, 0, 0, displayW, displayH);

      // Brush strokes
      ctx.fillStyle = "rgba(255, 0, 0, 0.4)";
      for (const s of strokes) {
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
        ctx.fill();
      }
    };
    img.src = person.segmentedImage;

    return () => {
      cancelled = true;
    };
  }, [person.segmentedImage, strokes, displayW, displayH, expanded]);

  const getPos = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const handleMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      e.preventDefault();
      setIsDrawing(true);
      const pos = getPos(e);
      setStrokes((prev) => [...prev, { ...pos, radius: brushSize }]);
    },
    [brushSize]
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isDrawing) return;
      e.preventDefault();
      const pos = getPos(e);
      setStrokes((prev) => [...prev, { ...pos, radius: brushSize }]);
    },
    [isDrawing, brushSize]
  );

  const handleMouseUp = useCallback(() => {
    setIsDrawing(false);
  }, []);

  return (
    <div className="space-y-3">
      <p className={`text-gray-600 ${expanded ? "text-sm" : "text-xs"}`}>
        削除したい部分をなぞってください
      </p>
      <div className="flex justify-center">
        <canvas
          ref={canvasRef}
          className="border border-gray-300 rounded cursor-crosshair"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        />
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => setStrokes([])}
          className={`flex-1 border border-gray-300 rounded hover:bg-gray-50 transition-colors ${
            expanded ? "text-sm px-3 py-1.5" : "text-xs px-2 py-1"
          }`}
        >
          クリア
        </button>
        <button
          onClick={() => onApply(strokes, displayW, displayH)}
          disabled={strokes.length === 0 || isErasing}
          className={`flex-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors ${
            expanded ? "text-sm px-3 py-1.5" : "text-xs px-2 py-1"
          }`}
        >
          {isErasing ? "適用中..." : "消去を適用"}
        </button>
      </div>
    </div>
  );
}

/**
 * EraserPanel — always renders a SINGLE container div that toggles between
 * inline styling and fixed fullscreen styling via CSS classes.
 * This prevents React from unmounting/remounting children (especially the canvas)
 * when switching between compact and expanded views.
 * A backdrop overlay is rendered via portal only when expanded.
 */
export function EraserPanel({
  mode,
  target,
  person,
  regions,
  isDetecting,
  isErasing,
  brushSize,
  onBrushSizeChange,
  onAutoDetect,
  onBrushMode,
  onEraseRegions,
  onBrushApply,
  onClose,
}: EraserPanelProps) {
  const [expanded, setExpanded] = useState(false);

  if (mode === "off" || !target || !person) return null;

  const label = target === "person1" ? "人物1" : "人物2";

  return (
    <>
      {/* Backdrop — only when expanded, rendered via portal */}
      {expanded &&
        createPortal(
          <div
            className="fixed inset-0 bg-black/50 z-40"
            onClick={() => setExpanded(false)}
          />,
          document.body
        )}

      {/* Single container — toggles between inline and fixed via classes */}
      <div
        className={
          expanded
            ? "fixed inset-4 md:inset-8 lg:inset-16 bg-white rounded-2xl shadow-2xl z-50 flex flex-col overflow-hidden"
            : "border border-orange-300 bg-orange-50 rounded-lg p-3 space-y-3"
        }
      >
        {/* Header */}
        <div
          className={
            expanded
              ? "flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-orange-50 flex-shrink-0"
              : "flex items-center justify-between"
          }
        >
          {expanded ? (
            <h3 className="text-lg font-semibold text-orange-800">
              消しゴム - {label}
            </h3>
          ) : (
            <h4 className="text-sm font-semibold text-orange-800">
              消しゴム - {label}
            </h4>
          )}
          <div className="flex items-center gap-2">
            {expanded ? (
              <>
                <button
                  onClick={() => setExpanded(false)}
                  className="text-sm text-gray-600 hover:text-blue-600 border border-gray-300 rounded-lg px-3 py-1.5 hover:bg-gray-50 transition-colors"
                >
                  縮小
                </button>
                <button
                  onClick={() => {
                    setExpanded(false);
                    onClose();
                  }}
                  className="text-sm text-gray-500 hover:text-red-600 border border-gray-300 rounded-lg px-3 py-1.5 hover:bg-red-50 transition-colors"
                >
                  閉じる
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setExpanded(true)}
                  className="text-[10px] text-blue-600 hover:text-blue-800 border border-blue-300 rounded px-1.5 py-0.5 hover:bg-blue-50 transition-colors"
                >
                  拡大
                </button>
                <button
                  onClick={onClose}
                  className="text-xs text-gray-500 hover:text-red-600 transition-colors"
                >
                  閉じる
                </button>
              </>
            )}
          </div>
        </div>

        {/* Body */}
        <div className={expanded ? "flex-1 overflow-y-auto px-6 py-4" : ""}>
          <div className="space-y-3">
            {/* Mode selector */}
            <div className="flex gap-2">
              <button
                onClick={onAutoDetect}
                className={`flex-1 border rounded transition-colors ${
                  mode === "auto"
                    ? "bg-orange-200 border-orange-400 text-orange-800"
                    : "border-gray-300 text-gray-600 hover:bg-gray-50"
                } ${expanded ? "text-sm px-3 py-2" : "text-xs px-2 py-1.5"}`}
              >
                自動検出
              </button>
              <button
                onClick={onBrushMode}
                className={`flex-1 border rounded transition-colors ${
                  mode === "brush"
                    ? "bg-orange-200 border-orange-400 text-orange-800"
                    : "border-gray-300 text-gray-600 hover:bg-gray-50"
                } ${expanded ? "text-sm px-3 py-2" : "text-xs px-2 py-1.5"}`}
              >
                ブラシ
              </button>
            </div>

            {/* Auto detect */}
            {mode === "auto" &&
              (isDetecting ? (
                <div className="text-sm text-gray-500 text-center py-6">
                  領域を検出中...
                </div>
              ) : (
                <RegionSelector
                  regions={regions}
                  isErasing={isErasing}
                  onErase={onEraseRegions}
                  expanded={expanded}
                />
              ))}

            {/* Brush */}
            {mode === "brush" && (
              <>
                <div>
                  <label
                    className={`block text-gray-500 ${
                      expanded ? "text-sm" : "text-xs"
                    }`}
                  >
                    ブラシサイズ ({brushSize}px)
                  </label>
                  <input
                    type="range"
                    min={5}
                    max={expanded ? 120 : 80}
                    value={brushSize}
                    onChange={(e) => onBrushSizeChange(Number(e.target.value))}
                    className="w-full"
                  />
                </div>
                <BrushCanvas
                  person={person}
                  brushSize={brushSize}
                  isErasing={isErasing}
                  expanded={expanded}
                  onApply={onBrushApply}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
