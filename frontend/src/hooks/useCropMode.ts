import { useState, useCallback, useRef } from "react";

export interface CropRect {
  startX: number;
  startY: number;
  endX: number;
  endY: number;
}

const MIN_CROP_SIZE = 0.01; // Minimum 1% of canvas dimension

interface UseCropModeReturn {
  isCropMode: boolean;
  cropRect: CropRect | null;
  isDrawing: boolean;
  enableCropMode: () => void;
  disableCropMode: () => void;
  handleCropMouseDown: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleCropMouseMove: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  handleCropMouseUp: () => void;
  getNormalizedCrop: () => { x1: number; y1: number; x2: number; y2: number } | null;
  resetCrop: () => void;
}

export function useCropMode(): UseCropModeReturn {
  const [isCropMode, setIsCropMode] = useState(false);
  const [cropRect, setCropRect] = useState<CropRect | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const drawingRef = useRef(false);
  // Store the last valid (confirmed) crop rect so accidental clicks don't destroy it
  const confirmedCropRef = useRef<CropRect | null>(null);

  const enableCropMode = useCallback(() => {
    setIsCropMode(true);
    // Default: select entire canvas area
    const defaultRect: CropRect = { startX: 0, startY: 0, endX: 1, endY: 1 };
    setCropRect(defaultRect);
    confirmedCropRef.current = defaultRect;
  }, []);

  const disableCropMode = useCallback(() => {
    setIsCropMode(false);
    setCropRect(null);
    confirmedCropRef.current = null;
    setIsDrawing(false);
    drawingRef.current = false;
  }, []);

  const resetCrop = useCallback(() => {
    setCropRect(null);
    confirmedCropRef.current = null;
    setIsDrawing(false);
    drawingRef.current = false;
  }, []);

  const getRelativePos = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    return {
      x: Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width)),
      y: Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height)),
    };
  };

  const isValidCropRect = (rect: CropRect): boolean => {
    const w = Math.abs(rect.endX - rect.startX);
    const h = Math.abs(rect.endY - rect.startY);
    return w >= MIN_CROP_SIZE && h >= MIN_CROP_SIZE;
  };

  const handleCropMouseDown = useCallback(
    (e: React.MouseEvent<HTMLCanvasElement>) => {
      if (!isCropMode) return;
      const pos = getRelativePos(e);
      // Start drawing a new rect (visual feedback during drag)
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
    // On mouseUp, check if the drawn rect is valid
    // If valid, confirm it; if not, restore the previous confirmed rect
    setCropRect((current) => {
      if (current && isValidCropRect(current)) {
        confirmedCropRef.current = current;
        return current;
      }
      // Drawn rect was too small (accidental click) - restore previous
      return confirmedCropRef.current;
    });
  }, []);

  const getNormalizedCrop = useCallback(() => {
    if (!cropRect) return null;
    const x1 = Math.min(cropRect.startX, cropRect.endX);
    const y1 = Math.min(cropRect.startY, cropRect.endY);
    const x2 = Math.max(cropRect.startX, cropRect.endX);
    const y2 = Math.max(cropRect.startY, cropRect.endY);
    if (x2 - x1 < MIN_CROP_SIZE || y2 - y1 < MIN_CROP_SIZE) return null;
    return { x1, y1, x2, y2 };
  }, [cropRect]);

  return {
    isCropMode,
    cropRect,
    isDrawing,
    enableCropMode,
    disableCropMode,
    handleCropMouseDown,
    handleCropMouseMove,
    handleCropMouseUp,
    getNormalizedCrop,
    resetCrop,
  };
}
