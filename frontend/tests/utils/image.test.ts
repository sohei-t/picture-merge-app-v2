import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  validateImageFile,
  base64ToBlob,
  generateDownloadFilename,
  downloadImage,
} from "../../src/utils/image.ts";

describe("validateImageFile", () => {
  it("accepts JPEG files within size limit", () => {
    const file = new File(["x".repeat(100)], "photo.jpg", { type: "image/jpeg" });
    const result = validateImageFile(file);
    expect(result.valid).toBe(true);
    expect(result.error).toBeUndefined();
  });

  it("accepts PNG files within size limit", () => {
    const file = new File(["x".repeat(100)], "photo.png", { type: "image/png" });
    const result = validateImageFile(file);
    expect(result.valid).toBe(true);
  });

  it("accepts WebP files within size limit", () => {
    const file = new File(["x".repeat(100)], "photo.webp", { type: "image/webp" });
    const result = validateImageFile(file);
    expect(result.valid).toBe(true);
  });

  it("rejects unsupported file types", () => {
    const file = new File(["x"], "doc.pdf", { type: "application/pdf" });
    const result = validateImageFile(file);
    expect(result.valid).toBe(false);
    expect(result.error).toContain("対応していないファイル形式");
  });

  it("rejects GIF files", () => {
    const file = new File(["x"], "anim.gif", { type: "image/gif" });
    const result = validateImageFile(file);
    expect(result.valid).toBe(false);
    expect(result.error).toContain("JPEG/PNG/WebP");
  });

  it("rejects files exceeding 20MB", () => {
    // Create a file object with a mocked size
    const file = new File(["x"], "big.jpg", { type: "image/jpeg" });
    Object.defineProperty(file, "size", { value: 21 * 1024 * 1024 });
    const result = validateImageFile(file);
    expect(result.valid).toBe(false);
    expect(result.error).toContain("20MB");
  });

  it("accepts files exactly at 20MB", () => {
    const file = new File(["x"], "exact.jpg", { type: "image/jpeg" });
    Object.defineProperty(file, "size", { value: 20 * 1024 * 1024 });
    const result = validateImageFile(file);
    expect(result.valid).toBe(true);
  });
});

describe("base64ToBlob", () => {
  it("converts a PNG data URI to a Blob", () => {
    // btoa("hello") = "aGVsbG8="
    const dataUri = "data:image/png;base64,aGVsbG8=";
    const blob = base64ToBlob(dataUri);
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.type).toBe("image/png");
    expect(blob.size).toBe(5); // "hello" is 5 bytes
  });

  it("converts a JPEG data URI to a Blob", () => {
    const dataUri = "data:image/jpeg;base64,dGVzdA==";
    const blob = base64ToBlob(dataUri);
    expect(blob.type).toBe("image/jpeg");
    expect(blob.size).toBe(4); // "test" is 4 bytes
  });

  it("falls back to image/png when mime is not matched", () => {
    // Construct a malformed header without proper mime pattern
    const dataUri = "invalid-header,aGVsbG8=";
    const blob = base64ToBlob(dataUri);
    expect(blob.type).toBe("image/png");
  });
});

describe("generateDownloadFilename", () => {
  it("returns a filename starting with merged_", () => {
    const name = generateDownloadFilename();
    expect(name).toMatch(/^merged_/);
  });

  it("returns a filename ending with .png", () => {
    const name = generateDownloadFilename();
    expect(name).toMatch(/\.png$/);
  });

  it("contains a timestamp-like pattern", () => {
    const name = generateDownloadFilename();
    // Pattern: merged_YYYY-MM-DDTHH-MM-SS.png
    expect(name).toMatch(/^merged_\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.png$/);
  });
});

describe("downloadImage", () => {
  let appendChildSpy: ReturnType<typeof vi.spyOn>;
  let removeChildSpy: ReturnType<typeof vi.spyOn>;
  let createObjectURLSpy: ReturnType<typeof vi.spyOn>;
  let revokeObjectURLSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    appendChildSpy = vi.spyOn(document.body, "appendChild").mockImplementation((node) => node);
    removeChildSpy = vi.spyOn(document.body, "removeChild").mockImplementation((node) => node);
    createObjectURLSpy = vi.fn(() => "blob:mock-download-url") as unknown as ReturnType<typeof vi.spyOn>;
    revokeObjectURLSpy = vi.fn() as unknown as ReturnType<typeof vi.spyOn>;
    globalThis.URL.createObjectURL = createObjectURLSpy;
    globalThis.URL.revokeObjectURL = revokeObjectURLSpy;
  });

  it("creates a link element, clicks it, and cleans up", () => {
    const clickSpy = vi.fn();
    const createElementSpy = vi.spyOn(document, "createElement").mockReturnValue({
      href: "",
      download: "",
      click: clickSpy,
    } as unknown as HTMLAnchorElement);

    const dataUri = "data:image/png;base64,aGVsbG8=";
    downloadImage(dataUri);

    expect(createElementSpy).toHaveBeenCalledWith("a");
    expect(clickSpy).toHaveBeenCalled();
    expect(appendChildSpy).toHaveBeenCalled();
    expect(removeChildSpy).toHaveBeenCalled();
    expect(revokeObjectURLSpy).toHaveBeenCalledWith("blob:mock-download-url");

    createElementSpy.mockRestore();
  });

  it("sets the download filename on the anchor element", () => {
    let capturedDownload = "";
    const createElementSpy = vi.spyOn(document, "createElement").mockReturnValue({
      href: "",
      set download(val: string) {
        capturedDownload = val;
      },
      get download() {
        return capturedDownload;
      },
      click: vi.fn(),
    } as unknown as HTMLAnchorElement);

    downloadImage("data:image/png;base64,aGVsbG8=");

    expect(capturedDownload).toMatch(/^merged_.*\.png$/);

    createElementSpy.mockRestore();
  });
});
