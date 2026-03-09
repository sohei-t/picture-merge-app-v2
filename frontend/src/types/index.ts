// ===== Application Phase =====
export type AppPhase =
  | "IDLE"
  | "ONE_UPLOADED"
  | "SEGMENTING"
  | "PREVIEW"
  | "MERGING"
  | "COMPLETE"
  | "ERROR";

// ===== Image Size =====
export interface ImageSize {
  width: number;
  height: number;
}

// ===== Bounding Box =====
export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

// ===== Segmentation Result =====
export interface SegmentationResult {
  id: string;
  segmentedImage: string;
  bbox: BoundingBox;
  footY: number;
  originalSize: ImageSize;
  processingTimeMs: number;
}

// ===== API Response Types =====
export interface SegmentResponse {
  id: string;
  segmented_image: string;
  bbox: BoundingBox;
  foot_y: number;
  original_size: ImageSize;
  processing_time_ms: number;
}

export interface MergeResponse {
  merged_image: string;
  processing_time_ms: number;
  output_size: ImageSize;
}

export interface HealthResponse {
  status: string;
  rembg_loaded: boolean;
  version: string;
}

export interface ApiError {
  error: string;
  message: string;
  detail?: string;
}

// ===== Merge Settings =====
export interface PersonSettings {
  x: number;
  yOffset: number;
  scale: number;
}

export interface ShadowSettings {
  enabled: boolean;
  intensity: number;
}

export type OutputPreset = "square" | "landscape" | "portrait" | "custom";

export interface OutputSize {
  width: number;
  height: number;
  preset: OutputPreset;
}

export type LayerOrder = "person1_back" | "person2_back";

export interface MergeSettings {
  backgroundColor: string;
  outputSize: OutputSize;
  person1: PersonSettings;
  person2: PersonSettings;
  shadow: ShadowSettings;
  colorCorrection: boolean;
  layerOrder: LayerOrder;
}

// ===== Merge Request (API format) =====
export interface MergeRequest {
  image1_id: string;
  image2_id: string;
  settings: {
    background_color: string;
    output_width: number;
    output_height: number;
    person1: {
      x: number;
      y_offset: number;
      scale: number;
    };
    person2: {
      x: number;
      y_offset: number;
      scale: number;
    };
    shadow: {
      enabled: boolean;
      intensity: number;
    };
    color_correction: boolean;
    layer_order: string;
  };
  preview_mode: boolean;
}

// ===== App Error =====
export interface AppError {
  type: "validation" | "network" | "segmentation" | "merge" | "unknown";
  message: string;
  detail?: string;
  retryable: boolean;
}

// ===== Output Size Presets =====
export const OUTPUT_PRESETS: Record<OutputPreset, { width: number; height: number; label: string }> = {
  square:    { width: 1024, height: 1024, label: "正方形 (1024x1024)" },
  landscape: { width: 1280, height: 720,  label: "横長 16:9 (1280x720)" },
  portrait:  { width: 720,  height: 1280, label: "縦長 9:16 (720x1280)" },
  custom:    { width: 1024, height: 1024, label: "カスタム" },
};

// ===== Default Settings =====
export const DEFAULT_MERGE_SETTINGS: MergeSettings = {
  backgroundColor: "#FFFFFF",
  outputSize: { width: 1024, height: 1024, preset: "square" },
  person1: { x: 0.3, yOffset: 0, scale: 1.0 },
  person2: { x: 0.7, yOffset: 0, scale: 1.0 },
  shadow: { enabled: true, intensity: 0.5 },
  colorCorrection: true,
  layerOrder: "person1_back",
};
