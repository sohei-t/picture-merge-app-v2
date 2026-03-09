import { useState, useCallback, useRef } from "react";

export interface CropRect {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

interface UseCropModeReturn {
  isCropMode: boolean;
  cropRect: CropRect | null;
  isDrawing: boolean;
  enableCropMode: () => void;
  disableCropMode: () => void;
  handleCropMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleCropMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleCropMouseUp: () => void;
  executeCrop: (previewImage: string) => void;
  resetCrop: () => void;
}

export function useCropMode(): UseCropModeReturn {
  const [isCropMode, setIsCropMode] = useState(false);
  const [cropRect, setCropRect] = useState<CropRect | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const drawingRef = useRef(false);

  const enableCropMode = useCallback(() => {
    setIsCropMode(true);
    setCropRect(null);
  }, []);

  const disableCropMode = useCallback(() => {
    setIsCropMode(false);
    setCropRect(null);
    setIsDrawing(false);
    drawingRef.current = false;
  }, []);

  const resetCrop = useCallback(() => {
    setCropRect(null);
    setIsDrawing(false);
    drawingRef.current = false;
  }, []);

  const getRelativePos = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    return {
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
    };
  };

  const handleCropMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isCropMode) return;
      const pos = getRelativePos(e);
      setCropRect({ startX: pos.x, startY: pos.y, endX: pos.x, endY: pos.y });
      setIsDrawing(true);
      drawingRef.current = true;
    },
    [isCropMode]
  );

  const handleCropMouseMove = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!drawingRef.current) return;
      const pos = getRelativePos(e);
      setCropRect((prev) =>
        prev ? { ...prev, endX: pos.x, endY: pos.y } : null
      );
    },
    []
  );

  const handleCropMouseUp = useCallback(() => {
    if (!drawingRef.current) return;
    setIsDrawing(false);
    drawingRef.current = false;
  }, []);

  const executeCrop = useCallback(
    (previewImage: string) => {
      if (!cropRect) return;

      const img = new Image();
      img.onload = () => {
        const x1 = Math.min(cropRect.startX, cropRect.endX);
        const y1 = Math.min(cropRect.startY, cropRect.endY);
        const x2 = Math.max(cropRect.startX, cropRect.endX);
        const y2 = Math.max(cropRect.startY, cropRect.endY);

        const sx = Math.round(x1 * img.width);
        const sy = Math.round(y1 * img.height);
        const sw = Math.round((x2 - x1) * img.width);
        const sh = Math.round((y2 - y1) * img.height);

        if (sw < 10 || sh < 10) return;

        const canvas = document.createElement("canvas");
        canvas.width = sw;
        canvas.height = sh;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        ctx.drawImage(img, sx, sy, sw, sh, 0, 0, sw, sh);

        const dataUrl = canvas.toDataURL("image/png");
        const now = new Date();
        const timestamp = now.toISOString().replace(/[:.]/g, "-").slice(0, 19);
        const filename = `cropped_${timestamp}.png`;

        const blob = dataURLToBlob(dataUrl);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      };
      img.src = previewImage;
    },
    [cropRect]
  );

  return {
    isCropMode,
    cropRect,
    isDrawing,
    enableCropMode,
    disableCropMode,
    handleCropMouseDown,
    handleCropMouseMove,
    handleCropMouseUp,
    executeCrop,
    resetCrop,
  };
}

function dataURLToBlob(dataUrl: string): Blob {
  const [header, base64Data] = dataUrl.split(",");
  const mimeMatch = header.match(/data:(.*?);/);
  const mime = mimeMatch ? mimeMatch[1] : "image/png";
  const byteString = atob(base64Data);
  const ab = new ArrayBuffer(byteString.length);
  const ia = new Uint8Array(ab);
  for (let i = 0; i < byteString.length; i++) {
    ia[i] = byteString.charCodeAt(i);
  }
  return new Blob([ab], { type: mime });
}
