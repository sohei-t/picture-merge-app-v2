import { useState, useCallback, useRef } from "react";
import type { AdjustParams, AppError } from "../types/index.ts";
import { DEFAULT_ADJUST_PARAMS } from "../types/index.ts";
import { aiEnhance, adjustImage, resetImage } from "../api/client.ts";

interface EnhanceResult {
  segmentedImage: string;
  bbox: { x: number; y: number; width: number; height: number };
  footY: number;
}

interface UseEnhanceReturn {
  // AI enhancement
  isEnhancing: boolean;
  enhancedTargets: Set<string>; // seg_ids that have been AI-enhanced
  runAiEnhance: (segId: string) => Promise<EnhanceResult | null>;

  // Manual adjustment
  isAdjusting: boolean;
  adjustParams: Record<string, AdjustParams>; // per seg_id
  getAdjustParams: (segId: string) => AdjustParams;
  applyAdjust: (segId: string, params: AdjustParams) => Promise<EnhanceResult | null>;

  // Reset to original
  isResetting: boolean;
  resetToOriginal: (segId: string) => Promise<EnhanceResult | null>;

  error: AppError | null;
}

export function useEnhance(): UseEnhanceReturn {
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [isAdjusting, setIsAdjusting] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [enhancedTargets, setEnhancedTargets] = useState<Set<string>>(new Set());
  const [adjustParams, setAdjustParams] = useState<Record<string, AdjustParams>>({});
  const [error, setError] = useState<AppError | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const runAiEnhance = useCallback(async (segId: string): Promise<EnhanceResult | null> => {
    setIsEnhancing(true);
    setError(null);
    try {
      const res = await aiEnhance(segId);
      setEnhancedTargets((prev) => new Set(prev).add(segId));
      return {
        segmentedImage: res.segmented_image,
        bbox: res.bbox,
        footY: res.foot_y,
      };
    } catch (err) {
      setError(err as AppError);
      return null;
    } finally {
      setIsEnhancing(false);
    }
  }, []);

  const getAdjustParams = useCallback(
    (segId: string): AdjustParams => {
      return adjustParams[segId] ?? { ...DEFAULT_ADJUST_PARAMS };
    },
    [adjustParams]
  );

  const applyAdjust = useCallback(
    async (segId: string, params: AdjustParams): Promise<EnhanceResult | null> => {
      // Save params immediately for UI
      setAdjustParams((prev) => ({ ...prev, [segId]: params }));

      // Debounce API call
      if (debounceRef.current) clearTimeout(debounceRef.current);

      return new Promise((resolve) => {
        debounceRef.current = setTimeout(async () => {
          setIsAdjusting(true);
          setError(null);
          try {
            const res = await adjustImage(segId, params);
            resolve({
              segmentedImage: res.segmented_image,
              bbox: res.bbox,
              footY: res.foot_y,
            });
          } catch (err) {
            setError(err as AppError);
            resolve(null);
          } finally {
            setIsAdjusting(false);
          }
        }, 300);
      });
    },
    []
  );

  const resetToOriginal = useCallback(async (segId: string): Promise<EnhanceResult | null> => {
    setIsResetting(true);
    setError(null);
    try {
      const res = await resetImage(segId);
      // Clear enhancement and adjustment state for this seg_id
      setEnhancedTargets((prev) => {
        const next = new Set(prev);
        next.delete(segId);
        return next;
      });
      setAdjustParams((prev) => {
        const next = { ...prev };
        delete next[segId];
        return next;
      });
      return {
        segmentedImage: res.segmented_image,
        bbox: res.bbox,
        footY: res.foot_y,
      };
    } catch (err) {
      setError(err as AppError);
      return null;
    } finally {
      setIsResetting(false);
    }
  }, []);

  return {
    isEnhancing,
    enhancedTargets,
    runAiEnhance,
    isAdjusting,
    adjustParams,
    getAdjustParams,
    applyAdjust,
    isResetting,
    resetToOriginal,
    error,
  };
}
