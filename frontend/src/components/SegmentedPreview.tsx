import type { SegmentationResult } from "../types/index.ts";

interface SegmentedPreviewProps {
  person1: SegmentationResult | null;
  person2: SegmentationResult | null;
}

export function SegmentedPreview({ person1, person2 }: SegmentedPreviewProps) {
  if (!person1 && !person2) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">切り抜き結果</h3>
      <div className="grid grid-cols-2 gap-2">
        {person1 && (
          <div className="bg-gray-100 rounded-lg p-2 flex items-center justify-center">
            <img
              src={person1.segmentedImage}
              alt="人物1 切り抜き"
              className="max-h-[120px] object-contain"
            />
          </div>
        )}
        {person2 && (
          <div className="bg-gray-100 rounded-lg p-2 flex items-center justify-center">
            <img
              src={person2.segmentedImage}
              alt="人物2 切り抜き"
              className="max-h-[120px] object-contain"
            />
          </div>
        )}
      </div>
    </div>
  );
}
