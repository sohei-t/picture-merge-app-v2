import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ImageDropzone } from "../../src/components/ImageDropzone.tsx";

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
    const file = new File(["dummy"], "test.jpg", { type: "image/jpeg" });
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
});
