import { useRef, useEffect } from "react";
import type { CropRect } from "../hooks/useCropMode.ts";

interface PersonHighlight {
  centerX: number; // 0-1 ratio
  topY: number;    // pixel offset from canvas top (in output coords)
  width: number;   // pixel width (in output coords)
  height: number;  // pixel height (in output coords)
}

interface PreviewCanvasProps {
  previewImage: string | null;
  isLoading: boolean;
  isCropMode?: boolean;
  cropRect?: CropRect | null;
  selectedPerson?: "person1" | "person2" | null;
  person1Highlight?: PersonHighlight | null;
  person2Highlight?: PersonHighlight | null;
  onMouseDown?: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  onMouseMove?: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  onMouseUp?: (e: React.MouseEvent<HTMLCanvasElement>) => void;
}

export function PreviewCanvas({
  previewImage,
  isLoading,
  isCropMode,
  cropRect,
  selectedPerson,
  person1Highlight,
  person2Highlight,
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
      drawOverlays(ctx, canvas.width, canvas.height, cropRect, selectedPerson, person1Highlight, person2Highlight);
    };
    img.src = previewImage;
  }, [previewImage, cropRect, selectedPerson, person1Highlight, person2Highlight]);

  // Redraw overlays when they change without reloading image
  useEffect(() => {
    if (!imageRef.current) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(imageRef.current, 0, 0);
    drawOverlays(ctx, canvas.width, canvas.height, cropRect, selectedPerson, person1Highlight, person2Highlight);
  }, [cropRect, selectedPerson, person1Highlight, person2Highlight]);

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
        onMouseLeave={onMouseUp as (() => void) | undefined}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/60 rounded-lg pointer-events-none">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      )}
      {isCropMode && (
        <div className="absolute top-2 left-2 bg-blue-600 text-white text-xs px-2 py-1 rounded">
          トリミングモード：範囲をドラッグで選択
        </div>
      )}
      {selectedPerson && !isCropMode && (
        <div className="absolute top-2 left-2 bg-cyan-600 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
          <span className="inline-block w-2 h-2 rounded-full bg-cyan-300 animate-pulse" />
          {selectedPerson === "person1" ? "人物1" : "人物2"} を選択中
        </div>
      )}
    </div>
  );
}

function drawOverlays(
  ctx: CanvasRenderingContext2D,
  canvasW: number,
  canvasH: number,
  cropRect: CropRect | null | undefined,
  selectedPerson: "person1" | "person2" | null | undefined,
  person1Highlight: PersonHighlight | null | undefined,
  person2Highlight: PersonHighlight | null | undefined,
) {
  // Draw selection highlight
  if (selectedPerson && !cropRect) {
    const hl = selectedPerson === "person1" ? person1Highlight : person2Highlight;
    if (hl) {
      drawSelectionGlow(ctx, canvasW, canvasH, hl);
    }
  }

  // Draw crop overlay
  if (cropRect) {
    drawCropOverlay(ctx, canvasW, canvasH, cropRect);
  }
}

function drawSelectionGlow(
  ctx: CanvasRenderingContext2D,
  canvasW: number,
  canvasH: number,
  hl: PersonHighlight,
) {
  // Scale highlight coords from output space to canvas (preview) space
  // We don't know the exact output dimensions, but highlight values are in ratio/output coords
  // centerX is 0-1 ratio, others are in output pixels
  // We need to map to canvas pixels
  const cx = hl.centerX * canvasW;
  const halfW = (hl.width / 2) * (canvasW / canvasW); // already in proportional space via caller
  const x = cx - halfW;
  const y = hl.topY;
  const w = hl.width;
  const h = hl.height;

  // Outer glow
  ctx.save();
  ctx.shadowColor = "rgba(0, 200, 255, 0.8)";
  ctx.shadowBlur = 20;
  ctx.strokeStyle = "rgba(0, 200, 255, 0.7)";
  ctx.lineWidth = 3;
  ctx.setLineDash([]);

  // Draw rounded rect glow
  const pad = 6;
  const rx = x - pad;
  const ry = y - pad;
  const rw = w + pad * 2;
  const rh = h + pad * 2;
  const radius = 8;
  drawRoundedRect(ctx, rx, ry, rw, rh, radius);
  ctx.stroke();

  // Second pass for stronger glow
  ctx.shadowBlur = 10;
  ctx.strokeStyle = "rgba(0, 220, 255, 0.4)";
  ctx.lineWidth = 6;
  drawRoundedRect(ctx, rx - 2, ry - 2, rw + 4, rh + 4, radius + 2);
  ctx.stroke();

  ctx.restore();

  // Corner markers
  ctx.save();
  ctx.strokeStyle = "rgba(0, 220, 255, 0.9)";
  ctx.lineWidth = 3;
  ctx.setLineDash([]);
  const markerLen = Math.min(20, rw / 4, rh / 4);
  // Top-left
  ctx.beginPath();
  ctx.moveTo(rx, ry + markerLen);
  ctx.lineTo(rx, ry);
  ctx.lineTo(rx + markerLen, ry);
  ctx.stroke();
  // Top-right
  ctx.beginPath();
  ctx.moveTo(rx + rw - markerLen, ry);
  ctx.lineTo(rx + rw, ry);
  ctx.lineTo(rx + rw, ry + markerLen);
  ctx.stroke();
  // Bottom-left
  ctx.beginPath();
  ctx.moveTo(rx, ry + rh - markerLen);
  ctx.lineTo(rx, ry + rh);
  ctx.lineTo(rx + markerLen, ry + rh);
  ctx.stroke();
  // Bottom-right
  ctx.beginPath();
  ctx.moveTo(rx + rw - markerLen, ry + rh);
  ctx.lineTo(rx + rw, ry + rh);
  ctx.lineTo(rx + rw, ry + rh - markerLen);
  ctx.stroke();
  ctx.restore();
}

function drawRoundedRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function drawCropOverlay(
  ctx: CanvasRenderingContext2D,
  canvasW: number,
  canvasH: number,
  cropRect: CropRect,
) {
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
