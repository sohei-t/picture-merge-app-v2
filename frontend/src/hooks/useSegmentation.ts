import { useState, useCallback } from "react";
import type { SegmentationResult, AppError } from "../types/index.ts";
import { segmentImage } from "../api/client.ts";

interface UseSegmentationReturn {
  person1: SegmentationResult | null;
  person2: SegmentationResult | null;
  isProcessing: boolean;
  error: AppError | null;
  segmentBoth: (file1: File, file2: File) => Promise<void>;
  segmentOne: (target: "person1" | "person2", file: File) => Promise<void>;
  clearPerson: (target: "person1" | "person2") => void;
  updatePerson: (
    target: "person1" | "person2",
    updates: { segmentedImage: string; bbox: { x: number; y: number; width: number; height: number }; footY: number }
  ) => void;
  reset: () => void;
}

function mapResponse(res: Awaited<ReturnType<typeof segmentImage>>): SegmentationResult {
  return {
    id: res.id,
    segmentedImage: res.segmented_image,
    bbox: res.bbox,
    footY: res.foot_y,
    originalSize: res.original_size,
    processingTimeMs: res.processing_time_ms,
    enhanced: res.enhanced ?? false,
    enhancementScale: res.enhancement_scale ?? 1,
  };
}

export function useSegmentation(): UseSegmentationReturn {
  const [person1, setPerson1] = useState<SegmentationResult | null>(null);
  const [person2, setPerson2] = useState<SegmentationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<AppError | null>(null);

  const segmentBoth = useCallback(async (file1: File, file2: File) => {
    setIsProcessing(true);
    setError(null);
    try {
      const [res1, res2] = await Promise.all([
        segmentImage(file1),
        segmentImage(file2),
      ]);
      setPerson1(mapResponse(res1));
      setPerson2(mapResponse(res2));
    } catch (err) {
      setError(err as AppError);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const segmentOne = useCallback(async (target: "person1" | "person2", file: File) => {
    setIsProcessing(true);
    setError(null);
    try {
      const res = await segmentImage(file);
      const result = mapResponse(res);
      if (target === "person1") {
        setPerson1(result);
      } else {
        setPerson2(result);
      }
    } catch (err) {
      setError(err as AppError);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const clearPerson = useCallback((target: "person1" | "person2") => {
    if (target === "person1") {
      setPerson1(null);
    } else {
      setPerson2(null);
    }
  }, []);

  const updatePerson = useCallback(
    (
      target: "person1" | "person2",
      updates: { segmentedImage: string; bbox: { x: number; y: number; width: number; height: number }; footY: number }
    ) => {
      const setter = target === "person1" ? setPerson1 : setPerson2;
      setter((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          segmentedImage: updates.segmentedImage,
          bbox: updates.bbox,
          footY: updates.footY,
        };
      });
    },
    []
  );

  const reset = useCallback(() => {
    setPerson1(null);
    setPerson2(null);
    setError(null);
    setIsProcessing(false);
  }, []);

  return { person1, person2, isProcessing, error, segmentBoth, segmentOne, clearPerson, updatePerson, reset };
}
