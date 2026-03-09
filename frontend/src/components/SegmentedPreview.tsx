import type { SegmentationResult } from "../types/index.ts";

interface SegmentedPreviewProps {
  person1: SegmentationResult | null;
  person2: SegmentationResult | null;
}

function EnhancedBadge({ result }: { result: SegmentationResult }) {
  if (!result.enhanced) return null;
  return (
    <span className="absolute top-1 right-1 bg-green-600 text-white text-[10px] px-1.5 py-0.5 rounded-full">
      {result.enhancementScale}x補正
    </span>
  );
}

export function SegmentedPreview({ person1, person2 }: SegmentedPreviewProps) {
  if (!person1 && !person2) return null;

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-gray-700">切り抜き結果</h3>
      <div className="grid grid-cols-2 gap-2">
        {person1 && (
          <div className="relative bg-gray-100 rounded-lg p-2 flex items-center justify-center">
            <img
              src={person1.segmentedImage}
              alt="人物1 切り抜き"
              className="max-h-[120px] object-contain"
            />
            <EnhancedBadge result={person1} />
          </div>
        )}
        {person2 && (
          <div className="relative bg-gray-100 rounded-lg p-2 flex items-center justify-center">
            <img
              src={person2.segmentedImage}
              alt="人物2 切り抜き"
              className="max-h-[120px] object-contain"
            />
            <EnhancedBadge result={person2} />
          </div>
        )}
      </div>
    </div>
  );
}
