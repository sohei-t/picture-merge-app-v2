import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { ImageDropzone } from "../../src/components/ImageDropzone.tsx";

// Helper to create a valid image file
function createImageFile(name = "test.jpg", type = "image/jpeg", size = 100): File {
  const file = new File(["x".repeat(size)], name, { type });
  return file;
}

// Helper to simulate a drop event with files
function createDropEvent(files: File[]): { dataTransfer: { files: File[]; items: DataTransferItem[]; types: string[] } } {
  return {
    dataTransfer: {
      files,
      items: files.map((file) => ({
        kind: "file",
        type: file.type,
        getAsFile: () => file,
      })) as unknown as DataTransferItem[],
      types: ["Files"],
    },
  };
}

describe("ImageDropzone", () => {
  it("renders label text", () => {
    render(
      <ImageDropzone
        label="人物1の写真"
        file={null}
        onDrop={vi.fn()}
        onError={vi.fn()}
      />
    );
    expect(screen.getByText("人物1の写真")).toBeInTheDocument();
  });

  it("shows upload instructions when no file", () => {
    render(
      <ImageDropzone
        label="テスト"
        file={null}
        onDrop={vi.fn()}
        onError={vi.fn()}
      />
    );
    expect(screen.getByText("写真をドラッグ＆ドロップ")).toBeInTheDocument();
    expect(screen.getByText(/JPEG \/ PNG \/ WebP/)).toBeInTheDocument();
  });

  it("shows thumbnail when file is provided", () => {
    const file = createImageFile("test.jpg", "image/jpeg");
    render(
      <ImageDropzone
        label="テスト"
        file={file}
        onDrop={vi.fn()}
        onError={vi.fn()}
      />
    );
    const img = screen.getByAltText("サムネイル");
    expect(img).toBeInTheDocument();
  });

  it("applies disabled styling", () => {
    const { container } = render(
      <ImageDropzone
        label="テスト"
        file={null}
        onDrop={vi.fn()}
        onError={vi.fn()}
        disabled
      />
    );
    const dropzone = container.querySelector("[class*='opacity-50']");
    expect(dropzone).not.toBeNull();
  });

  it("calls onDrop when a valid file is dropped", async () => {
    const onDrop = vi.fn();
    const onError = vi.fn();
    const { container } = render(
      <ImageDropzone
        label="テスト"
        file={null}
        onDrop={onDrop}
        onError={onError}
      />
    );

    const dropzone = container.querySelector("[class*='border-dashed']") as HTMLElement;
    const file = createImageFile("photo.png", "image/png");

    await act(async () => {
      fireEvent.drop(dropzone, createDropEvent([file]));
    });

    expect(onDrop).toHaveBeenCalledWith(file);
    expect(onError).not.toHaveBeenCalled();
  });

  it("calls onError when rejected file (wrong type) is dropped", async () => {
    const onDrop = vi.fn();
    const onError = vi.fn();
    const { container } = render(
      <ImageDropzone
        label="テスト"
        file={null}
        onDrop={onDrop}
        onError={onError}
      />
    );

    const dropzone = container.querySelector("[class*='border-dashed']") as HTMLElement;
    const file = new File(["data"], "doc.pdf", { type: "application/pdf" });

    await act(async () => {
      fireEvent.drop(dropzone, createDropEvent([file]));
    });

    expect(onDrop).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith(
      expect.stringContaining("対応していないファイル形式")
    );
  });

  it("calls onError when file exceeds max size", async () => {
    const onDrop = vi.fn();
    const onError = vi.fn();
    const { container } = render(
      <ImageDropzone
        label="テスト"
        file={null}
        onDrop={onDrop}
        onError={onError}
      />
    );

    const dropzone = container.querySelector("[class*='border-dashed']") as HTMLElement;
    const file = new File(["x"], "big.jpg", { type: "image/jpeg" });
    Object.defineProperty(file, "size", { value: 25 * 1024 * 1024 });

    await act(async () => {
      fireEvent.drop(dropzone, createDropEvent([file]));
    });

    // react-dropzone should reject it due to maxSize
    expect(onDrop).not.toHaveBeenCalled();
  });

  it("does not show thumbnail when file is null", () => {
    render(
      <ImageDropzone
        label="テスト"
        file={null}
        onDrop={vi.fn()}
        onError={vi.fn()}
      />
    );
    const img = screen.queryByAltText("サムネイル");
    expect(img).toBeNull();
  });

  it("renders with default disabled=false", () => {
    const { container } = render(
      <ImageDropzone
        label="テスト"
        file={null}
        onDrop={vi.fn()}
        onError={vi.fn()}
      />
    );
    const dropzone = container.querySelector("[class*='opacity-50']");
    expect(dropzone).toBeNull();
  });
});
