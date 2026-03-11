import { useState, useCallback, useEffect, useMemo } from "react";
import type { AppPhase, MergeSettings, AppError } from "./types/index.ts";
import { DEFAULT_MERGE_SETTINGS } from "./types/index.ts";
import { healthCheck } from "./api/client.ts";
import { downloadImage } from "./utils/image.ts";
import { useSegmentation } from "./hooks/useSegmentation.ts";
import { useMerge } from "./hooks/useMerge.ts";
import { useCanvasDrag } from "./hooks/useCanvasDrag.ts";
import { useCropMode } from "./hooks/useCropMode.ts";
import { useEraser } from "./hooks/useEraser.ts";
import { Header } from "./components/Header.tsx";
import { ImageDropzone } from "./components/ImageDropzone.tsx";
import { SegmentedPreview } from "./components/SegmentedPreview.tsx";
import { SettingsPanel } from "./components/SettingsPanel.tsx";
import { PreviewCanvas } from "./components/PreviewCanvas.tsx";
import { DownloadButton } from "./components/DownloadButton.tsx";
import { StatusIndicator } from "./components/StatusIndicator.tsx";
import { EraserPanel } from "./components/EraserPanel.tsx";

function App() {
  // ===== Server connection =====
  const [isServerConnected, setIsServerConnected] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const checkHealth = async () => {
      try {
        await healthCheck();
        if (!cancelled) setIsServerConnected(true);
      } catch {
        if (!cancelled) setIsServerConnected(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // ===== Phase state =====
  const [phase, setPhase] = useState<AppPhase>("IDLE");
  const [file1, setFile1] = useState<File | null>(null);
  const [file2, setFile2] = useState<File | null>(null);
  const [settings, setSettings] = useState<MergeSettings>(DEFAULT_MERGE_SETTINGS);
  const [appError, setAppError] = useState<AppError | null>(null);

  // ===== Hooks =====
  const segmentation = useSegmentation();
  const merge = useMerge();
  const crop = useCropMode();
  const eraser = useEraser();

  // ===== Derived error =====
  const displayError = appError ?? segmentation.error ?? merge.error ?? eraser.error;

  // ===== File handlers =====
  const handleFile1 = useCallback(
    (file: File) => {
      setFile1(file);
      setAppError(null);
      merge.reset();
      crop.disableCropMode();
      eraser.close();
      if (file2) {
        setPhase("SEGMENTING");
        segmentation.segmentBoth(file, file2).then(() => {
          setPhase("PREVIEW");
        }).catch(() => {
          setPhase("ERROR");
        });
      } else {
        setPhase("ONE_UPLOADED");
        segmentation.segmentOne("person1", file).catch(() => {});
      }
    },
    [file2, segmentation, merge, crop, eraser]
  );

  const handleFile2 = useCallback(
    (file: File) => {
      setFile2(file);
      setAppError(null);
      merge.reset();
      crop.disableCropMode();
      eraser.close();
      if (file1) {
        setPhase("SEGMENTING");
        segmentation.segmentBoth(file1, file).then(() => {
          setPhase("PREVIEW");
        }).catch(() => {
          setPhase("ERROR");
        });
      } else {
        setPhase("ONE_UPLOADED");
        segmentation.segmentOne("person2", file).catch(() => {});
      }
    },
    [file1, segmentation, merge, crop, eraser]
  );

  // ===== Per-person clear =====
  const handleClear1 = useCallback(() => {
    setFile1(null);
    segmentation.clearPerson("person1");
    merge.reset();
    crop.disableCropMode();
    eraser.close();
    setPhase(file2 ? "ONE_UPLOADED" : "IDLE");
  }, [file2, segmentation, merge, crop, eraser]);

  const handleClear2 = useCallback(() => {
    setFile2(null);
    segmentation.clearPerson("person2");
    merge.reset();
    crop.disableCropMode();
    eraser.close();
    setPhase(file1 ? "ONE_UPLOADED" : "IDLE");
  }, [file1, segmentation, merge, crop, eraser]);

  const handleFileError = useCallback((message: string) => {
    setAppError({
      type: "validation",
      message,
      retryable: false,
    });
  }, []);

  // ===== Settings change triggers preview =====
  const handleSettingsChange = useCallback(
    (newSettings: MergeSettings) => {
      setSettings(newSettings);
      if (segmentation.person1 && segmentation.person2) {
        merge.fetchPreview(
          segmentation.person1.id,
          segmentation.person2.id,
          newSettings
        );
      }
    },
    [segmentation.person1, segmentation.person2, merge]
  );

  // ===== Trigger preview after segmentation =====
  useEffect(() => {
    if (phase === "PREVIEW" && segmentation.person1 && segmentation.person2 && !merge.previewImage) {
      merge.fetchPreview(
        segmentation.person1.id,
        segmentation.person2.id,
        settings
      );
    }
  }, [phase, segmentation.person1, segmentation.person2, settings, merge]);

  // ===== Download =====
  const handleDownload = useCallback(async () => {
    if (!segmentation.person1 || !segmentation.person2) return;
    setPhase("MERGING");
    try {
      const response = await merge.fetchFullResolution(
        segmentation.person1.id,
        segmentation.person2.id,
        settings
      );
      downloadImage(response.merged_image);
      setPhase("COMPLETE");
    } catch {
      setPhase("ERROR");
    }
  }, [segmentation.person1, segmentation.person2, settings, merge]);

  // ===== Reset =====
  const handleReset = useCallback(() => {
    setPhase("IDLE");
    setFile1(null);
    setFile2(null);
    setSettings(DEFAULT_MERGE_SETTINGS);
    setAppError(null);
    segmentation.reset();
    merge.reset();
    eraser.close();
  }, [segmentation, merge, eraser]);

  // ===== Eraser handlers =====
  const handleEraserOpen = useCallback(
    (target: "person1" | "person2") => {
      const person = target === "person1" ? segmentation.person1 : segmentation.person2;
      if (!person) return;
      eraser.startAutoDetect(target, person.id);
    },
    [segmentation.person1, segmentation.person2, eraser]
  );

  const handleEraseRegions = useCallback(
    async (regionIds: number[]) => {
      if (!eraser.target) return;
      const person = eraser.target === "person1" ? segmentation.person1 : segmentation.person2;
      if (!person) return;

      const result = await eraser.eraseSelectedRegions(person.id, regionIds);
      if (result) {
        segmentation.updatePerson(eraser.target, {
          segmentedImage: result.segmentedImage,
          bbox: result.bbox,
          footY: result.footY,
        });
        // Refresh preview
        if (segmentation.person1 && segmentation.person2) {
          merge.fetchPreview(
            segmentation.person1.id,
            segmentation.person2.id,
            settings
          );
        }
      }
    },
    [eraser, segmentation, merge, settings]
  );

  const handleBrushApply = useCallback(
    async (
      strokes: { x: number; y: number; radius: number }[],
      displayWidth: number,
      displayHeight: number
    ) => {
      if (!eraser.target) return;
      const person = eraser.target === "person1" ? segmentation.person1 : segmentation.person2;
      if (!person) return;

      const result = await eraser.sendBrushStrokes(
        person.id,
        strokes,
        displayWidth,
        displayHeight
      );
      if (result) {
        segmentation.updatePerson(eraser.target, {
          segmentedImage: result.segmentedImage,
          bbox: result.bbox,
          footY: result.footY,
        });
        // Refresh preview
        if (segmentation.person1 && segmentation.person2) {
          merge.fetchPreview(
            segmentation.person1.id,
            segmentation.person2.id,
            settings
          );
        }
      }
    },
    [eraser, segmentation, merge, settings]
  );

  // ===== Compute person highlight positions for canvas overlay =====
  const person1Highlight = useMemo(() => {
    if (!segmentation.person1) return null;
    const bbox = segmentation.person1.bbox;
    const outW = settings.outputSize.width;
    const outH = settings.outputSize.height;
    const targetHeight = outH * 0.7;
    const scale = bbox.height > 0 ? (targetHeight / bbox.height) * settings.person1.scale : settings.person1.scale;
    const personW = bbox.width * scale;
    const personH = bbox.height * scale;
    const footLineY = outH * 0.8;
    const footRel = (segmentation.person1.footY - bbox.y) * scale;
    const topY = footLineY - footRel + settings.person1.yOffset;
    const previewMaxDim = 768;
    const ratio = Math.min(1, previewMaxDim / Math.max(outW, outH));
    return {
      centerX: settings.person1.x,
      topY: topY * ratio,
      width: personW * ratio,
      height: personH * ratio,
    };
  }, [segmentation.person1, settings]);

  const person2Highlight = useMemo(() => {
    if (!segmentation.person1 || !segmentation.person2) return null;
    const bbox1 = segmentation.person1.bbox;
    const bbox2 = segmentation.person2.bbox;
    const outW = settings.outputSize.width;
    const outH = settings.outputSize.height;
    const targetHeight = outH * 0.7;
    const p1H = bbox1.height;
    const p2H = bbox2.height;
    const autoRatio = p2H === 0 ? 1.0 : Math.max(0.8, Math.min(1.2, p1H / p2H));
    const scale = p2H > 0 ? (targetHeight / p2H) * autoRatio * settings.person2.scale : settings.person2.scale;
    const personW = bbox2.width * scale;
    const personH = bbox2.height * scale;
    const footLineY = outH * 0.8;
    const footRel = (segmentation.person2.footY - bbox2.y) * scale;
    const topY = footLineY - footRel + settings.person2.yOffset;
    const previewMaxDim = 768;
    const ratio = Math.min(1, previewMaxDim / Math.max(outW, outH));
    return {
      centerX: settings.person2.x,
      topY: topY * ratio,
      width: personW * ratio,
      height: personH * ratio,
    };
  }, [segmentation.person1, segmentation.person2, settings]);

  // ===== Canvas drag =====
  const drag = useCanvasDrag({
    person1Highlight,
    person2Highlight,
    outputWidth: settings.outputSize.width,
    outputHeight: settings.outputSize.height,
    person1X: settings.person1.x,
    person2X: settings.person2.x,
    person1YOffset: settings.person1.yOffset,
    person2YOffset: settings.person2.yOffset,
    onDragEnd: useCallback(
      (target: "person1" | "person2", newX: number, newYOffset: number) => {
        const newSettings = {
          ...settings,
          [target]: { ...settings[target], x: newX, yOffset: Math.round(newYOffset) },
        };
        setSettings(newSettings);
        if (segmentation.person1 && segmentation.person2) {
          merge.fetchPreview(
            segmentation.person1.id,
            segmentation.person2.id,
            newSettings
          );
        }
      },
      [settings, segmentation.person1, segmentation.person2, merge]
    ),
  });

  // ===== Crop with server-side cropping =====
  const handleCropExecute = useCallback(async () => {
    if (!segmentation.person1 || !segmentation.person2) return;
    const normalizedCrop = crop.getNormalizedCrop();
    if (!normalizedCrop) return;
    if (merge.isLoading) return;
    try {
      const response = await merge.fetchCropped(
        segmentation.person1.id,
        segmentation.person2.id,
        settings,
        normalizedCrop
      );
      downloadImage(response.merged_image, `cropped_${response.output_size.width}x${response.output_size.height}`);
    } catch (err) {
      console.error("Crop download failed:", err);
      if (!merge.error) {
        setAppError({
          type: "merge",
          message: "切り出しダウンロードに失敗しました。ページをリロードして再度お試しください。",
          retryable: true,
        });
      }
    }
  }, [segmentation.person1, segmentation.person2, settings, merge, crop]);

  // ===== Determine if controls should be disabled =====
  const isProcessing = segmentation.isProcessing || merge.isLoading;
  const canEdit = phase === "PREVIEW" || phase === "COMPLETE";

  // Get the active eraser person
  const eraserPerson = eraser.target === "person1" ? segmentation.person1 : eraser.target === "person2" ? segmentation.person2 : null;

  return (
    <div className="min-h-screen bg-gray-50">
      <Header serverConnected={isServerConnected} />

      <main className="max-w-[1600px] mx-auto px-4 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Panel: Image Upload + Segmentation Results */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-xl shadow-sm p-4 space-y-4">
              <h2 className="text-lg font-semibold text-gray-800">写真入力</h2>
              <ImageDropzone
                label="人物1の写真"
                file={file1}
                onDrop={handleFile1}
                onError={handleFileError}
                onClear={handleClear1}
                disabled={phase === "SEGMENTING" || phase === "MERGING"}
              />
              <ImageDropzone
                label="人物2の写真"
                file={file2}
                onDrop={handleFile2}
                onError={handleFileError}
                onClear={handleClear2}
                disabled={phase === "SEGMENTING" || phase === "MERGING"}
              />
            </div>

            <div className="bg-white rounded-xl shadow-sm p-4">
              <SegmentedPreview
                person1={segmentation.person1}
                person2={segmentation.person2}
                onErase={canEdit ? handleEraserOpen : undefined}
                eraserActive={eraser.target}
              />
            </div>

            {/* Eraser Panel */}
            {eraser.mode !== "off" && (
              <div className="bg-white rounded-xl shadow-sm p-4">
                <EraserPanel
                  mode={eraser.mode}
                  target={eraser.target}
                  person={eraserPerson}
                  regions={eraser.regions}
                  isDetecting={eraser.isDetecting}
                  isErasing={eraser.isErasing}
                  brushSize={eraser.brushSize}
                  onBrushSizeChange={eraser.setBrushSize}
                  onAutoDetect={() => {
                    if (eraser.target) {
                      const p = eraser.target === "person1" ? segmentation.person1 : segmentation.person2;
                      if (p) eraser.startAutoDetect(eraser.target, p.id);
                    }
                  }}
                  onBrushMode={() => {
                    if (eraser.target) eraser.startBrushMode(eraser.target);
                  }}
                  onEraseRegions={handleEraseRegions}
                  onBrushApply={handleBrushApply}
                  onClose={eraser.close}
                />
              </div>
            )}

            <div className="bg-white rounded-xl shadow-sm p-4">
              <StatusIndicator
                phase={phase}
                error={displayError}
                processingTimeMs={merge.processingTimeMs}
              />
            </div>
          </div>

          {/* Center: Preview + Download */}
          <div className="lg:col-span-1 space-y-4">
            <div className="bg-white rounded-xl shadow-sm p-4">
              <h2 className="text-lg font-semibold text-gray-800 mb-3">合成プレビュー</h2>
              <PreviewCanvas
                previewImage={merge.previewImage}
                isLoading={merge.isLoading}
                isCropMode={crop.isCropMode}
                cropRect={crop.cropRect}
                selectedPerson={drag.selectedPerson}
                person1Highlight={person1Highlight}
                person2Highlight={person2Highlight}
                onMouseDown={
                  canEdit
                    ? crop.isCropMode
                      ? crop.handleCropMouseDown
                      : drag.handleMouseDown
                    : undefined
                }
                onMouseMove={
                  canEdit
                    ? crop.isCropMode
                      ? crop.handleCropMouseMove
                      : drag.handleMouseMove
                    : undefined
                }
                onMouseUp={
                  canEdit
                    ? crop.isCropMode
                      ? crop.handleCropMouseUp
                      : drag.handleMouseUp
                    : undefined
                }
              />
            </div>

            <div className="bg-white rounded-xl shadow-sm p-4">
              <DownloadButton
                phase={phase}
                onDownload={handleDownload}
                onReset={handleReset}
                isMerging={merge.isLoading}
                isCropMode={crop.isCropMode}
                isCropping={merge.isLoading && crop.isCropMode}
                hasCropRect={!!crop.cropRect}
                onCropToggle={crop.isCropMode ? crop.disableCropMode : crop.enableCropMode}
                onCropExecute={handleCropExecute}
              />
            </div>
          </div>

          {/* Right Panel: Settings */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-xl shadow-sm p-4 lg:sticky lg:top-4 lg:max-h-[calc(100vh-2rem)] lg:overflow-y-auto">
              <SettingsPanel
                settings={settings}
                onChange={handleSettingsChange}
                disabled={!canEdit || isProcessing}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
