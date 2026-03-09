const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_FILE_SIZE = 20 * 1024 * 1024; // 20MB

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

export function validateImageFile(file: File): FileValidationResult {
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return {
      valid: false,
      error: "対応していないファイル形式です。JPEG/PNG/WebPファイルを使用してください。",
    };
  }

  if (file.size > MAX_FILE_SIZE) {
    return {
      valid: false,
      error: "ファイルサイズが20MBを超えています。",
    };
  }

  return { valid: true };
}

export function base64ToBlob(dataUri: string): Blob {
  const [header, base64Data] = dataUri.split(",");
  const mimeMatch = header.match(/data:(.*?);/);
  const mime = mimeMatch ? mimeMatch[1] : "image/png";
  const byteString = atob(base64Data);
  const arrayBuffer = new ArrayBuffer(byteString.length);
  const uint8Array = new Uint8Array(arrayBuffer);
  for (let i = 0; i < byteString.length; i++) {
    uint8Array[i] = byteString.charCodeAt(i);
  }
  return new Blob([arrayBuffer], { type: mime });
}

export function generateDownloadFilename(): string {
  const now = new Date();
  const timestamp = now.toISOString().replace(/[:.]/g, "-").slice(0, 19);
  return `merged_${timestamp}.png`;
}

export function downloadImage(dataUri: string): void {
  const blob = base64ToBlob(dataUri);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = generateDownloadFilename();
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
