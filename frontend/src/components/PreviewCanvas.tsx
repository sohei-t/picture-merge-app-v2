import { useRef, useEffect } from "react";

interface PreviewCanvasProps {
  previewImage: string | null;
  isLoading: boolean;
  onMouseDown?: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  onMouseMove?: (e: React.MouseEvent<HTMLCanvasElement>) => void;
  onMouseUp?: () => void;
}

export function PreviewCanvas({
  previewImage,
  isLoading,
  onMouseDown,
  onMouseMove,
  onMouseUp,
}: PreviewCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    if (!previewImage) {
      canvas.width = 512;
      canvas.height = 512;
      ctx.fillStyle = "#f3f4f6";
      ctx.fillRect(0, 0, 512, 512);
      ctx.fillStyle = "#9ca3af";
      ctx.font = "16px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("プレビューがここに表示されます", 256, 256);
      return;
    }

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
    };
    img.src = previewImage;
  }, [previewImage]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        className="w-full max-w-[640px] rounded-lg border border-gray-200 bg-gray-100"
        style={{ cursor: onMouseDown ? "grab" : "default" }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onMouseLeave={onMouseUp}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/60 rounded-lg">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
        </div>
      )}
    </div>
  );
}
