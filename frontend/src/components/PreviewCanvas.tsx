import { useRef, useEffect } from "react";
import type { CropRect } from "../hooks/useCropMode.ts";

interface PreviewCanvasProps {
  previewImage: string | null;
  isLoading: boolean;
  isCropMode?: boolean;
  cropRect?: CropRect | null;
  onMouseDown?: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  onMouseMove?: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  onMouseUp?: () => void;
}

export function PreviewCanvas({
  previewImage,
  isLoading,
  isCropMode,
  cropRect,
  onMouseDown,
  onMouseMove,
  onMouseUp,
}: PreviewCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (!previewImage) {
      canvas.width = 512;
      canvas.height = 512;
      ctx.fillStyle = "#f3f4f6";
      ctx.fillRect(0, 0, 512, 512);
      ctx.fillStyle = "#9ca3af";
      ctx.font = "16px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("プレビューがここに表示されます", 256, 256);
      imageRef.current = null;
      return;
    }

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
      imageRef.current = img;
      drawCropOverlay(ctx, canvas.width, canvas.height, cropRect);
    };
    img.src = previewImage;
  }, [previewImage, cropRect]);

  // Redraw crop overlay when cropRect changes without reloading image
  useEffect(() => {
    if (!cropRect || !imageRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(imageRef.current, 0, 0);
    drawCropOverlay(ctx, canvas.width, canvas.height, cropRect);
  }, [cropRect]);

  const cursor = isCropMode ? "crosshair" : onMouseDown ? "grab" : "default";

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        className="w-full max-w-[640px] rounded-lg border border-gray-200 bg-gray-100"
        style={{ cursor }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/60 rounded-lg">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      )}
      {isCropMode && (
        <div className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded">
          トリミングモード：範囲をドラッグで選択
        </div>
      )}
    </div>
  );
}

function drawCropOverlay(
  ctx: CanvasRenderingContext2D,
  canvasW: number,
  canvasH: number,
  cropRect: CropRect | null | undefined
) {
  if (!cropRect) return;

  const x1 = Math.min(cropRect.startX, cropRect.endX) * canvasW;
  const y1 = Math.min(cropRect.startY, cropRect.endY) * canvasH;
  const x2 = Math.max(cropRect.startX, cropRect.endX) * canvasW;
  const y2 = Math.max(cropRect.startY, cropRect.endY) * canvasH;
  const w = x2 - x1;
  const h = y2 - y1;

  if (w < 2 || h < 2) return;

  // Darken outside crop area
  ctx.fillStyle = "rgba(0, 0, 0, 0.4)";
  ctx.fillRect(0, 0, canvasW, y1);
  ctx.fillRect(0, y1, x1, h);
  ctx.fillRect(x2, y1, canvasW - x2, h);
  ctx.fillRect(0, y2, canvasW, canvasH - y2);

  // Draw selection border
  ctx.strokeStyle = "#3b82f6";
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 3]);
  ctx.strokeRect(x1, y1, w, h);
  ctx.setLineDash([]);

  // Draw dimension label
  const cropW = Math.round(w);
  const cropH = Math.round(h);
  ctx.fillStyle = "rgba(59, 130, 246, 0.8)";
  const label = `${cropW} × ${cropH}`;
  ctx.font = "12px sans-serif";
  const textMetrics = ctx.measureText(label);
  const labelX = x1 + w / 2 - textMetrics.width / 2 - 4;
  const labelY = y1 > 24 ? y1 - 8 : y1 + 4;
  ctx.fillRect(labelX, labelY - 12, textMetrics.width + 8, 18);
  ctx.fillStyle = "#ffffff";
  ctx.fillText(label, labelX + 4, labelY + 2);
}
