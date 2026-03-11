import { useState, useCallback } from "react";
import type { DetectedRegion, AppError } from "../types/index.ts";
import { detectRegions, eraseRegions, eraseManual } from "../api/client.ts";

export type EraserMode = "off" | "auto" | "brush";

interface UseEraserReturn {
  mode: EraserMode;
  target: "person1" | "person2" | null;
  regions: DetectedRegion[];
  isDetecting: boolean;
  isErasing: boolean;
  error: AppError | null;
  brushSize: number;
  setBrushSize: (size: number) => void;
  startAutoDetect: (
    target: "person1" | "person2",
    segId: string
  ) => Promise<void>;
  eraseSelectedRegions: (
    segId: string,
    regionIds: number[]
  ) => Promise<{ segmentedImage: string; bbox: { x: number; y: number; width: number; height: number }; footY: number } | null>;
  startBrushMode: (target: "person1" | "person2") => void;
  sendBrushStrokes: (
    segId: string,
    strokes: { x: number; y: number; radius: number }[],
    displayWidth: number,
    displayHeight: number
  ) => Promise<{ segmentedImage: string; bbox: { x: number; y: number; width: number; height: number }; footY: number } | null>;
  close: () => void;
}

export function useEraser(): UseEraserReturn {
  const [mode, setMode] = useState<EraserMode>("off");
  const [target, setTarget] = useState<"person1" | "person2" | null>(null);
  const [regions, setRegions] = useState<DetectedRegion[]>([]);
  const [isDetecting, setIsDetecting] = useState(false);
  const [isErasing, setIsErasing] = useState(false);
  const [error, setError] = useState<AppError | null>(null);
  const [brushSize, setBrushSize] = useState(20);

  const startAutoDetect = useCallback(
    async (t: "person1" | "person2", segId: string) => {
      setMode("auto");
      setTarget(t);
      setRegions([]);
      setIsDetecting(true);
      setError(null);
      try {
        const res = await detectRegions(segId);
        setRegions(res.regions);
      } catch (err) {
        setError(err as AppError);
      } finally {
        setIsDetecting(false);
      }
    },
    []
  );

  const eraseSelectedRegions = useCallback(
    async (segId: string, regionIds: number[]) => {
      setIsErasing(true);
      setError(null);
      try {
        const res = await eraseRegions(segId, regionIds);
        setMode("off");
        setTarget(null);
        setRegions([]);
        return {
          segmentedImage: res.segmented_image,
          bbox: res.bbox,
          footY: res.foot_y,
        };
      } catch (err) {
        setError(err as AppError);
        return null;
      } finally {
        setIsErasing(false);
      }
    },
    []
  );

  const startBrushMode = useCallback((t: "person1" | "person2") => {
    setMode("brush");
    setTarget(t);
    setRegions([]);
    setError(null);
  }, []);

  const sendBrushStrokes = useCallback(
    async (
      segId: string,
      strokes: { x: number; y: number; radius: number }[],
      displayWidth: number,
      displayHeight: number
    ) => {
      setIsErasing(true);
      setError(null);
      try {
        const res = await eraseManual(segId, strokes, displayWidth, displayHeight);
        return {
          segmentedImage: res.segmented_image,
          bbox: res.bbox,
          footY: res.foot_y,
        };
      } catch (err) {
        setError(err as AppError);
        return null;
      } finally {
        setIsErasing(false);
      }
    },
    []
  );

  const close = useCallback(() => {
    setMode("off");
    setTarget(null);
    setRegions([]);
    setError(null);
  }, []);

  return {
    mode,
    target,
    regions,
    isDetecting,
    isErasing,
    error,
    brushSize,
    setBrushSize,
    startAutoDetect,
    eraseSelectedRegions,
    startBrushMode,
    sendBrushStrokes,
    close,
  };
}
