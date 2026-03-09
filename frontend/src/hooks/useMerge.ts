import { useState, useCallback, useRef, useEffect } from "react";
import type { MergeSettings, MergeResponse, AppError } from "../types/index.ts";
import { mergeImages } from "../api/client.ts";

interface UseMergeReturn {
  previewImage: string | null;
  isLoading: boolean;
  error: AppError | null;
  processingTimeMs: number | null;
  fetchPreview: (image1Id: string, image2Id: string, settings: MergeSettings) => void;
  fetchFullResolution: (image1Id: string, image2Id: string, settings: MergeSettings) => Promise<MergeResponse>;
  reset: () => void;
}

function buildRequest(
  image1Id: string,
  image2Id: string,
  settings: MergeSettings,
  previewMode: boolean
) {
  return {
    image1_id: image1Id,
    image2_id: image2Id,
    settings: {
      background_color: settings.backgroundColor,
      output_width: settings.outputSize.width,
      output_height: settings.outputSize.height,
      person1: {
        x: settings.person1.x,
        y_offset: settings.person1.yOffset,
        scale: settings.person1.scale,
      },
      person2: {
        x: settings.person2.x,
        y_offset: settings.person2.yOffset,
        scale: settings.person2.scale,
      },
      shadow: {
        enabled: settings.shadow.enabled,
        intensity: settings.shadow.intensity,
      },
      color_correction: settings.colorCorrection,
      layer_order: settings.layerOrder,
    },
    preview_mode: previewMode,
  };
}

export function useMerge(): UseMergeReturn {
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<AppError | null>(null);
  const [processingTimeMs, setProcessingTimeMs] = useState<number | null>(null);
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  const fetchPreview = useCallback(
    (image1Id: string, image2Id: string, settings: MergeSettings) => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }

      debounceTimer.current = setTimeout(async () => {
        setIsLoading(true);
        setError(null);
        try {
          const request = buildRequest(image1Id, image2Id, settings, true);
          const response = await mergeImages(request);
          setPreviewImage(response.merged_image);
          setProcessingTimeMs(response.processing_time_ms);
        } catch (err) {
          setError(err as AppError);
        } finally {
          setIsLoading(false);
        }
      }, 300);
    },
    []
  );

  const fetchFullResolution = useCallback(
    async (image1Id: string, image2Id: string, settings: MergeSettings): Promise<MergeResponse> => {
      setIsLoading(true);
      setError(null);
      try {
        const request = buildRequest(image1Id, image2Id, settings, false);
        const response = await mergeImages(request);
        setProcessingTimeMs(response.processing_time_ms);
        return response;
      } catch (err) {
        setError(err as AppError);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const reset = useCallback(() => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }
    setPreviewImage(null);
    setIsLoading(false);
    setError(null);
    setProcessingTimeMs(null);
  }, []);

  return { previewImage, isLoading, error, processingTimeMs, fetchPreview, fetchFullResolution, reset };
}
