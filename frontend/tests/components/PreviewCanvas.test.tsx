import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { PreviewCanvas } from "../../src/components/PreviewCanvas.tsx";

describe("PreviewCanvas", () => {
  it("renders canvas element", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={false} />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas).not.toBeNull();
  });

  it("shows loading spinner when isLoading", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={true} />
    );
    const spinner = container.querySelector("[class*='animate-spin']");
    expect(spinner).not.toBeNull();
  });

  it("does not show loading spinner when not loading", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={false} />
    );
    const spinner = container.querySelector("[class*='animate-spin']");
    expect(spinner).toBeNull();
  });

  it("sets cursor to grab when drag handlers provided", () => {
    const { container } = render(
      <PreviewCanvas
        previewImage={null}
        isLoading={false}
        onMouseDown={vi.fn()}
        onMouseMove={vi.fn()}
        onMouseUp={vi.fn()}
      />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas?.style.cursor).toBe("grab");
  });

  it("sets cursor to default when no drag handlers", () => {
    const { container } = render(
      <PreviewCanvas previewImage={null} isLoading={false} />
    );
    const canvas = container.querySelector("canvas");
    expect(canvas?.style.cursor).toBe("default");
  });
});
