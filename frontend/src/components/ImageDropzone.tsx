import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { validateImageFile } from "../utils/image.ts";

interface ImageDropzoneProps {
  label: string;
  file: File | null;
  onDrop: (file: File) => void;
  onError: (message: string) => void;
  disabled?: boolean;
}

const ACCEPT = {
  "image/jpeg": [".jpg", ".jpeg"],
  "image/png": [".png"],
  "image/webp": [".webp"],
};

export function ImageDropzone({ label, file, onDrop, onError, disabled = false }: ImageDropzoneProps) {
  const handleDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: readonly { readonly errors: readonly { message: string }[] }[]) => {
      if (rejectedFiles.length > 0) {
        onError("対応していないファイル形式です。JPEG/PNG/WebPファイルを使用してください。");
        return;
      }
      if (acceptedFiles.length === 0) return;

      const file = acceptedFiles[0];
      const validation = validateImageFile(file);
      if (!validation.valid) {
        onError(validation.error ?? "ファイルのバリデーションに失敗しました。");
        return;
      }
      onDrop(file);
    },
    [onDrop, onError]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleDrop,
    accept: ACCEPT,
    maxSize: 20 * 1024 * 1024,
    multiple: false,
    disabled,
  });

  const thumbnailUrl = file ? URL.createObjectURL(file) : null;

  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">{label}</label>
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-lg p-4 text-center cursor-pointer
          transition-colors min-h-[160px] flex items-center justify-center
          ${disabled ? "opacity-50 cursor-not-allowed bg-gray-50" : ""}
          ${isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-gray-400"}
          ${file ? "border-green-400 bg-green-50" : ""}
        `}
      >
        <input {...getInputProps()} />
        {thumbnailUrl ? (
          <img
            src={thumbnailUrl}
            alt="サムネイル"
            className="max-h-[140px] max-w-full object-contain rounded"
          />
        ) : (
          <div className="text-gray-500">
            {isDragActive ? (
              <p className="text-blue-600 font-medium">ここにドロップ</p>
            ) : (
              <>
                <p className="mb-1">写真をドラッグ＆ドロップ</p>
                <p className="text-xs text-gray-400">
                  またはクリックしてファイルを選択
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  JPEG / PNG / WebP（最大20MB）
                </p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
