import { useState, useCallback, useRef, useEffect } from "react";
import type { MergeSettings, MergeResponse, AppError } from "../types/index.ts";
import { mergeImages } from "../api/client.ts";

interface CropRegion {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

interface UseMergeReturn {
  previewImage: string | null;
  isLoading: boolean;
  error: AppError | null;
  processingTimeMs: number | null;
  fetchPreview: (image1Id: string, image2Id: string, settings: MergeSettings) => void;
  fetchFullResolution: (image1Id: string, image2Id: string, settings: MergeSettings) => Promise<MergeResponse>;
  fetchCropped: (image1Id: string, image2Id: string, settings: MergeSettings, crop: CropRegion) => Promise<MergeResponse>;
  reset: () => void;
}

// Clamp value to [min, max] range
function clamp(v: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, v));
}

function buildRequest(
  image1Id: string,
  image2Id: string,
  settings: MergeSettings,
  previewMode: boolean,
  outputFormat: "PNG" | "JPEG" = "PNG",
) {
  return {
    image1_id: image1Id,
    image2_id: image2Id,
    settings: {
      background_color: settings.backgroundColor,
      output_width: clamp(settings.outputSize.width, 64, 4096),
      output_height: clamp(settings.outputSize.height, 64, 4096),
      person1: {
        x: clamp(settings.person1.x, -0.5, 1.5),
        y_offset: Math.round(clamp(settings.person1.yOffset, -2000, 2000)),
        scale: clamp(settings.person1.scale, 0.5, 2.0),
        rotation: clamp(settings.person1.rotation, -45, 45),
        flip_h: settings.person1.flipH,
        flip_v: settings.person1.flipV,
      },
      person2: {
        x: clamp(settings.person2.x, -0.5, 1.5),
        y_offset: Math.round(clamp(settings.person2.yOffset, -2000, 2000)),
        scale: clamp(settings.person2.scale, 0.5, 2.0),
        rotation: clamp(settings.person2.rotation, -45, 45),
        flip_h: settings.person2.flipH,
        flip_v: settings.person2.flipV,
      },
      shadow: {
        enabled: settings.shadow.enabled,
        intensity: clamp(settings.shadow.intensity, 0, 1),
      },
      color_correction: settings.colorCorrection,
      layer_order: settings.layerOrder,
    },
    preview_mode: previewMode,
    output_format: outputFormat,
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

  const fetchCropped = useCallback(
    async (image1Id: string, image2Id: string, settings: MergeSettings, crop: CropRegion): Promise<MergeResponse> => {
      setIsLoading(true);
      setError(null);
      try {
        const request = {
          ...buildRequest(image1Id, image2Id, settings, false, "PNG"),
          crop: { x1: crop.x1, y1: crop.y1, x2: crop.x2, y2: crop.y2 },
        };
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

  return { previewImage, isLoading, error, processingTimeMs, fetchPreview, fetchFullResolution, fetchCropped, reset };
}
